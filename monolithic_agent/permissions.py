"""
Custom Permission Classes for AlgoAgent
========================================

Ownership-based access control for user resources.
"""

from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit/delete it.
    
    - Read permissions are allowed to any authenticated user
    - Write permissions are only allowed to the owner of the object
    """
    
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any authenticated user
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions are only allowed to the owner
        # Check for different owner field names
        if hasattr(obj, 'created_by'):
            return obj.created_by == request.user
        elif hasattr(obj, 'user'):
            return obj.user == request.user
        elif hasattr(obj, 'author'):
            return obj.author == request.user
        
        # If no owner field exists, deny access
        return False


class IsOwner(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to view or modify it.
    
    Both read and write permissions are only allowed to the owner.
    """
    
    def has_object_permission(self, request, view, obj):
        # Check for different owner field names
        if hasattr(obj, 'created_by'):
            return obj.created_by == request.user
        elif hasattr(obj, 'user'):
            return obj.user == request.user
        elif hasattr(obj, 'author'):
            return obj.author == request.user
        
        # If no owner field exists, deny access
        return False


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Custom permission to only allow owners or admin users to access an object.
    
    Both read and write permissions are allowed to:
    - The owner of the object
    - Admin/superuser accounts
    """
    
    def has_object_permission(self, request, view, obj):
        # Admin users have full access
        if request.user and request.user.is_staff:
            return True
        
        # Check for different owner field names
        if hasattr(obj, 'created_by'):
            return obj.created_by == request.user
        elif hasattr(obj, 'user'):
            return obj.user == request.user
        elif hasattr(obj, 'author'):
            return obj.author == request.user
        
        # If no owner field exists, deny access
        return False


class IsAuthenticatedOrReadOnly(permissions.BasePermission):
    """
    Allow read-only access to unauthenticated users,
    but require authentication for write operations.
    """
    
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated
