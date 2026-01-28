# Ownership-Based Access Control Implementation Guide

## Overview

This guide documents the implementation of ownership-based access control (RBAC) for the AlgoAgent monolithic backend. The changes ensure that users can only view and manage their own resources (strategies, backtests, templates, etc.).

## Changes Implemented

### 1. Custom Permission Classes

**File:** `monolithic_agent/permissions.py` (NEW)

Three custom permission classes have been created:

#### `IsOwner`
- **Purpose:** Restricts both read and write access to resource owners only
- **Usage:** Applied to resources that should be completely private (strategies, backtests, etc.)
- **Logic:** Checks if `obj.created_by`, `obj.user`, or `obj.author` equals `request.user`

#### `IsOwnerOrReadOnly`
- **Purpose:** Allows read access to authenticated users but write access only to owners
- **Usage:** Applied to resources where users might read others' content but only modify their own
- **Logic:** SAFE_METHODS (GET, HEAD, OPTIONS) allowed to all authenticated users; write methods only for owners

#### `IsOwnerOrAdmin`
- **Purpose:** Allows full access to owners and admin/staff users
- **Usage:** Can be used for resources where admins need oversight capabilities
- **Logic:** Checks `request.user.is_staff` OR ownership

---

### 2. Strategy API Updates

**File:** `strategy_api/views.py`

#### StrategyTemplateViewSet
```python
permission_classes = [IsAuthenticated, IsOwner]

def get_queryset(self):
    """Users can only access their own templates"""
    if self.request.user.is_authenticated:
        return StrategyTemplate.objects.filter(created_by=self.request.user)
    return StrategyTemplate.objects.none()
```
- **Before:** AllowAny - all templates visible to everyone
- **After:** Only templates created by the logged-in user are visible

#### StrategyViewSet
```python
permission_classes = [IsAuthenticated, IsOwner]

def get_queryset(self):
    """Filter strategies by user and query parameters"""
    if not self.request.user.is_authenticated:
        return Strategy.objects.none()
    queryset = Strategy.objects.filter(created_by=self.request.user)
    # ... additional filters
```
- **Before:** AllowAny - all strategies visible to everyone
- **After:** Only strategies created by the logged-in user are visible
- **Impact:** Users see only their own strategies in list/detail endpoints

#### StrategyValidationViewSet
```python
permission_classes = [IsAuthenticated]

def get_queryset(self):
    """Users can only see validations for their own strategies"""
    if not self.request.user.is_authenticated:
        return StrategyValidation.objects.none()
    return StrategyValidation.objects.filter(strategy__created_by=self.request.user)
```
- Validations are filtered based on strategy ownership

#### StrategyPerformanceViewSet
```python
permission_classes = [IsAuthenticated]

def get_queryset(self):
    """Users can only see performance records for their own strategies"""
    if not self.request.user.is_authenticated:
        return StrategyPerformance.objects.none()
    return StrategyPerformance.objects.filter(strategy__created_by=self.request.user)
```
- Performance metrics visible only for user's own strategies

#### StrategyCommentViewSet
```python
permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]

def get_queryset(self):
    """Users can only see comments on their own strategies"""
    if not self.request.user.is_authenticated:
        return StrategyComment.objects.none()
    return StrategyComment.objects.filter(strategy__created_by=self.request.user)
```
- Comments filtered by strategy ownership
- Users can edit/delete only their own comments (via IsOwnerOrReadOnly)

#### StrategyChatViewSet
```python
permission_classes = [IsAuthenticated, IsOwner]

def get_queryset(self):
    """Users can only access their own chat sessions"""
    if not self.request.user.is_authenticated:
        return StrategyChat.objects.none()
    queryset = StrategyChat.objects.filter(user=self.request.user)
```
- **Before:** Conditional filtering with query param `my_sessions`
- **After:** Always filters by user automatically

---

### 3. Backtest API Updates

**File:** `backtest_api/views.py`

#### BacktestConfigViewSet
```python
permission_classes = [IsAuthenticated, IsOwner]

def get_queryset(self):
    """Users can only access their own backtest configs"""
    if not self.request.user.is_authenticated:
        return BacktestConfig.objects.none()
    return BacktestConfig.objects.filter(created_by=self.request.user)
```
- Only backtest configurations created by user are visible

#### BacktestRunViewSet
```python
permission_classes = [IsAuthenticated, IsOwner]

def get_queryset(self):
    """Filter backtest runs by user and query parameters"""
    if not self.request.user.is_authenticated:
        return BacktestRun.objects.none()
    queryset = BacktestRun.objects.filter(created_by=self.request.user)
```
- Only backtest runs created by user are visible
- Existing filters (status, strategy, symbols) still work but scoped to user's data

#### BacktestResultViewSet
```python
permission_classes = [IsAuthenticated]

def get_queryset(self):
    """Users can only see results for their own backtest runs"""
    if not self.request.user.is_authenticated:
        return BacktestResult.objects.none()
    return BacktestResult.objects.filter(run__created_by=self.request.user)
```
- Results filtered via backtest run ownership

#### TradeViewSet
```python
permission_classes = [IsAuthenticated]

def get_queryset(self):
    """Filter trades by user and query parameters"""
    if not self.request.user.is_authenticated:
        return Trade.objects.none()
    queryset = Trade.objects.filter(run__created_by=self.request.user)
```
- Trades filtered via backtest run ownership
- Existing filters (run_id, symbol, trade_type, status) still work

#### BacktestAlertViewSet
```python
permission_classes = [IsAuthenticated]

def get_queryset(self):
    """Users can only see alerts for their own backtest runs"""
    if not self.request.user.is_authenticated:
        return BacktestAlert.objects.none()
    return BacktestAlert.objects.filter(run__created_by=self.request.user)
```
- Alerts filtered via backtest run ownership

---

## Security Improvements

### Before Implementation
- ❌ Any user could view ALL strategies from ALL users
- ❌ Any user could view ALL backtest results
- ❌ Users could potentially modify/delete other users' data
- ❌ No authentication required for most endpoints

### After Implementation
- ✅ Users see only their own strategies
- ✅ Users see only their own backtest runs and results
- ✅ Authentication required for all data access
- ✅ Object-level permissions prevent unauthorized modifications
- ✅ Consistent ownership filtering across all related resources

---

## Frontend Impact

### Required Changes

1. **Authentication Headers**
   - All API requests MUST include JWT token in Authorization header
   - Format: `Authorization: Bearer <access_token>`

2. **Error Handling**
   - Handle `401 Unauthorized` responses (token expired/invalid)
   - Handle `403 Forbidden` responses (insufficient permissions)
   - Handle `404 Not Found` (resource doesn't exist or doesn't belong to user)

3. **User Experience**
   - Users will only see their own data (expected behavior)
   - No need to filter by "my strategies" manually anymore
   - Login required to access any strategy or backtest data

### Example Frontend Code

```javascript
// Before (worked without auth)
fetch('http://localhost:8000/api/strategies/')
  .then(response => response.json())

// After (requires authentication)
const token = localStorage.getItem('access_token');
fetch('http://localhost:8000/api/strategies/', {
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  }
})
  .then(response => {
    if (response.status === 401) {
      // Token expired, redirect to login or refresh token
      refreshToken();
    }
    return response.json();
  })
```

---

## Testing the Implementation

### Test Scenarios

1. **Create two test users**
   ```bash
   # User A
   POST /api/auth/register/
   {
     "username": "user_a",
     "email": "usera@example.com",
     "password": "password123"
   }
   
   # User B
   POST /api/auth/register/
   {
     "username": "user_b",
     "email": "userb@example.com",
     "password": "password123"
   }
   ```

2. **Create strategies as both users**
   ```bash
   # Login as User A, create strategy
   POST /api/strategies/
   Headers: Authorization: Bearer <user_a_token>
   {
     "name": "User A Strategy",
     "description": "Test",
     "strategy_code": "..."
   }
   
   # Login as User B, create strategy
   POST /api/strategies/
   Headers: Authorization: Bearer <user_b_token>
   {
     "name": "User B Strategy",
     "description": "Test",
     "strategy_code": "..."
   }
   ```

3. **Verify isolation**
   ```bash
   # User A can only see their strategy
   GET /api/strategies/
   Headers: Authorization: Bearer <user_a_token>
   # Should return only "User A Strategy"
   
   # User B can only see their strategy
   GET /api/strategies/
   Headers: Authorization: Bearer <user_b_token>
   # Should return only "User B Strategy"
   ```

4. **Test unauthorized access**
   ```bash
   # Try to access User B's strategy with User A's token
   GET /api/strategies/<user_b_strategy_id>/
   Headers: Authorization: Bearer <user_a_token>
   # Should return 404 Not Found
   
   # Try to update User B's strategy with User A's token
   PATCH /api/strategies/<user_b_strategy_id>/
   Headers: Authorization: Bearer <user_a_token>
   # Should return 404 Not Found or 403 Forbidden
   ```

---

## Database Schema Notes

### Ownership Fields Already Present

All models already have ownership tracking fields:
- `Strategy.created_by` → ForeignKey(User)
- `StrategyTemplate.created_by` → ForeignKey(User)
- `BacktestConfig.created_by` → ForeignKey(User)
- `BacktestRun.created_by` → ForeignKey(User)
- `StrategyChat.user` → ForeignKey(User)
- `AIContext.user` → ForeignKey(User)
- `StrategyComment.author` → ForeignKey(User)

**No database migrations required!** The fields exist; we're just enforcing their use.

---

## Future Enhancements (Optional)

### 1. Sharing Strategies
Add ability to share strategies with specific users or make them public:

```python
class Strategy(models.Model):
    # ... existing fields ...
    is_public = models.BooleanField(default=False)
    shared_with = models.ManyToManyField(User, related_name='shared_strategies', blank=True)
```

Update queryset:
```python
def get_queryset(self):
    user = self.request.user
    return Strategy.objects.filter(
        Q(created_by=user) |           # Own strategies
        Q(is_public=True) |             # Public strategies
        Q(shared_with=user)             # Explicitly shared
    )
```

### 2. Team/Organization Support
Add organization model for team collaboration:

```python
class Organization(models.Model):
    name = models.CharField(max_length=200)
    members = models.ManyToManyField(User, through='OrganizationMembership')

class OrganizationMembership(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=[('admin', 'Admin'), ('member', 'Member')])

class Strategy(models.Model):
    # ... existing fields ...
    organization = models.ForeignKey(Organization, null=True, blank=True)
```

### 3. Admin Dashboard
Create admin-only endpoints to view all users' data for monitoring:

```python
@action(detail=False, methods=['get'], permission_classes=[IsAdminUser])
def admin_all_strategies(self, request):
    """Admin-only: View all strategies across all users"""
    strategies = Strategy.objects.all()
    # ... return data
```

---

## Rollback Plan

If issues arise, you can temporarily revert to previous behavior:

1. **Quick revert** (keep authentication but remove filtering):
   ```python
   # In each ViewSet
   permission_classes = [AllowAny]  # Restore AllowAny
   
   # Comment out or remove get_queryset filters
   # def get_queryset(self):
   #     return ModelName.objects.all()
   ```

2. **Complete revert**:
   - Delete `permissions.py`
   - Restore original `strategy_api/views.py` and `backtest_api/views.py` from git

---

## Summary

This implementation provides a solid foundation for multi-user access control in AlgoAgent. Each user's data is completely isolated from other users, ensuring privacy and security while maintaining all existing functionality within the user's own data scope.

**Key Benefits:**
- ✅ Complete data isolation between users
- ✅ No data leakage or unauthorized access
- ✅ Consistent behavior across all resources
- ✅ No database changes required
- ✅ Easy to extend for future sharing features
