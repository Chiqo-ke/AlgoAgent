"""
Google OAuth Views for AlgoAgent
=================================

Handles Google OAuth authentication flow and token generation.
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from django.conf import settings
from django.shortcuts import redirect
from django.utils import timezone
import requests
import logging
import os

from .models import UserProfile

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([AllowAny])
def google_auth_redirect(request):
    """
    Redirect to Google OAuth consent screen.
    
    Query Parameters:
        redirect_uri: The frontend callback URL
    """
    redirect_uri = request.GET.get('redirect_uri', '')
    
    if not redirect_uri:
        return Response({
            'error': 'redirect_uri parameter is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    client_id = os.getenv('GOOGLE_OAUTH_CLIENT_ID')
    
    if not client_id:
        logger.error("GOOGLE_OAUTH_CLIENT_ID not configured")
        return Response({
            'error': 'Google OAuth not configured'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    # Build Google OAuth URL
    google_auth_url = (
        f"https://accounts.google.com/o/oauth2/v2/auth?"
        f"client_id={client_id}&"
        f"redirect_uri={redirect_uri}&"
        f"response_type=code&"
        f"scope=openid%20email%20profile&"
        f"access_type=online&"
        f"prompt=select_account"
    )
    
    logger.info(f"Redirecting to Google OAuth: {google_auth_url[:100]}...")
    return redirect(google_auth_url)


@api_view(['POST'])
@permission_classes([AllowAny])
def google_auth_callback(request):
    """
    Handle Google OAuth callback and exchange code for user tokens.
    
    Request Body:
        code: Authorization code from Google
        redirect_uri: The callback URL used in the initial request
        state: Optional state parameter
    
    Returns:
        access: JWT access token
        refresh: JWT refresh token
        user: User information
    """
    code = request.data.get('code')
    redirect_uri = request.data.get('redirect_uri')
    
    if not code or not redirect_uri:
        return Response({
            'error': 'code and redirect_uri are required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    client_id = os.getenv('GOOGLE_OAUTH_CLIENT_ID')
    client_secret = os.getenv('GOOGLE_OAUTH_CLIENT_SECRET')
    
    if not client_id or not client_secret:
        logger.error("Google OAuth credentials not configured")
        return Response({
            'error': 'Google OAuth not configured'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    try:
        # Exchange authorization code for access token
        token_url = 'https://oauth2.googleapis.com/token'
        token_data = {
            'code': code,
            'client_id': client_id,
            'client_secret': client_secret,
            'redirect_uri': redirect_uri,
            'grant_type': 'authorization_code'
        }
        
        logger.info("Exchanging Google OAuth code for token")
        token_response = requests.post(token_url, data=token_data)
        
        if token_response.status_code != 200:
            logger.error(f"Google token exchange failed: {token_response.text}")
            return Response({
                'error': 'Failed to exchange authorization code',
                'detail': token_response.json()
            }, status=status.HTTP_400_BAD_REQUEST)
        
        token_json = token_response.json()
        access_token = token_json.get('access_token')
        
        # Get user info from Google
        userinfo_url = 'https://www.googleapis.com/oauth2/v2/userinfo'
        userinfo_response = requests.get(
            userinfo_url,
            headers={'Authorization': f'Bearer {access_token}'}
        )
        
        if userinfo_response.status_code != 200:
            logger.error(f"Failed to get Google user info: {userinfo_response.text}")
            return Response({
                'error': 'Failed to retrieve user information'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        user_info = userinfo_response.json()
        
        # Extract user data
        email = user_info.get('email')
        google_id = user_info.get('id')
        first_name = user_info.get('given_name', '')
        last_name = user_info.get('family_name', '')
        picture = user_info.get('picture', '')
        
        if not email:
            return Response({
                'error': 'Email not provided by Google'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create or get user
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'username': email.split('@')[0] + '_' + google_id[:8],
                'first_name': first_name,
                'last_name': last_name,
            }
        )
        
        if created:
            logger.info(f"Created new user from Google OAuth: {user.username}")
            # Set unusable password for OAuth users
            user.set_unusable_password()
            user.save()
            
            # Create user profile with default preferences
            UserProfile.objects.create(
                user=user,
                trading_goals='New user authenticated via Google',
                risk_parameters={'auth_method': 'google'}
            )
        else:
            logger.info(f"Existing user logged in via Google: {user.username}")
            # Update last active
            if hasattr(user, 'profile'):
                user.profile.last_active = timezone.now()
                user.profile.save()
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
            },
            'message': 'Login successful' if not created else 'Account created successfully'
        }, status=status.HTTP_200_OK)
        
    except requests.RequestException as e:
        logger.error(f"Request error during Google OAuth: {str(e)}")
        return Response({
            'error': 'Failed to communicate with Google',
            'detail': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    except Exception as e:
        logger.error(f"Unexpected error during Google OAuth: {str(e)}")
        return Response({
            'error': 'Authentication failed',
            'detail': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
