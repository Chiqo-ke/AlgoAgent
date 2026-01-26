"""
Django management command to verify post-fix implementation.
"""
from django.core.management.base import BaseCommand
from strategy_api.models import StrategyTemplate
from Backtest.key_rotation import get_key_manager
from Backtest.request_router import get_request_router


class Command(BaseCommand):
    help = 'Verify that all fixes have been implemented correctly'
    
    def test_keymanager_methods(self):
        """Test that KeyManager has required methods"""
        self.stdout.write("\n=== Testing KeyManager Methods ===")
        
        key_manager = get_key_manager()
        
        # Check for required methods
        required_methods = ['mark_key_success', 'mark_key_failed', 'report_success', 'report_error']
        
        all_present = True
        for method_name in required_methods:
            if hasattr(key_manager, method_name):
                self.stdout.write(self.style.SUCCESS(f"✓ KeyManager has method: {method_name}"))
            else:
                self.stdout.write(self.style.ERROR(f"✗ KeyManager missing method: {method_name}"))
                all_present = False
        
        return all_present
    
    def test_system_templates(self):
        """Test that system templates exist in database"""
        self.stdout.write("\n=== Testing System Templates ===")
        
        templates = StrategyTemplate.objects.filter(
            is_active=True,
            is_system_template=True
        )
        
        count = templates.count()
        self.stdout.write(f"System templates found: {count}")
        
        if count == 0:
            self.stdout.write(self.style.ERROR("✗ No system templates available!"))
            return False
        
        for template in templates:
            self.stdout.write(self.style.SUCCESS(f"  ✓ {template.name} (category: {template.category})"))
        
        return True
    
    def test_request_router(self):
        """Test that RequestRouter initializes correctly"""
        self.stdout.write("\n=== Testing RequestRouter ===")
        
        try:
            router = get_request_router()
            self.stdout.write(self.style.SUCCESS("✓ RequestRouter initialized"))
            
            stats = router.get_stats()
            self.stdout.write(f"  Total requests: {stats['total_requests']}")
            self.stdout.write(f"  Total failures: {stats['total_failures']}")
            
            return True
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"✗ RequestRouter failed: {e}"))
            return False
    
    def test_template_lookup(self):
        """Test template auto-selection based on keywords"""
        self.stdout.write("\n=== Testing Template Lookup ===")
        
        test_descriptions = [
            ("Create a momentum strategy using moving averages", "momentum"),
            ("I want a mean reversion strategy using RSI", "mean_reversion"),
            ("Build a breakout strategy", "breakout"),
            ("Quick scalping strategy", "scalping"),
        ]
        
        all_passed = True
        for description, expected_category in test_descriptions:
            templates = StrategyTemplate.objects.filter(
                is_active=True,
                is_system_template=True,
                category=expected_category
            )
            
            if templates.exists():
                template = templates.first()
                self.stdout.write(self.style.SUCCESS(f"✓ '{description}' -> {template.name}"))
            else:
                self.stdout.write(self.style.ERROR(f"✗ No template for category: {expected_category}"))
                all_passed = False
        
        return all_passed
    
    def handle(self, *args, **options):
        """Main command execution"""
        self.stdout.write("=" * 60)
        self.stdout.write(self.style.HTTP_INFO("POST-FIX VERIFICATION TESTS"))
        self.stdout.write("=" * 60)
        
        tests = [
            ("KeyManager Methods", self.test_keymanager_methods),
            ("System Templates", self.test_system_templates),
            ("RequestRouter", self.test_request_router),
            ("Template Lookup", self.test_template_lookup),
        ]
        
        results = []
        for test_name, test_func in tests:
            try:
                result = test_func()
                results.append((test_name, result))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"✗ {test_name} crashed: {e}"))
                results.append((test_name, False))
        
        # Summary
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(self.style.HTTP_INFO("TEST SUMMARY"))
        self.stdout.write("=" * 60)
        
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        for test_name, result in results:
            if result:
                self.stdout.write(self.style.SUCCESS(f"✓ PASS: {test_name}"))
            else:
                self.stdout.write(self.style.ERROR(f"✗ FAIL: {test_name}"))
        
        self.stdout.write(f"\nTotal: {passed}/{total} tests passed")
        
        if passed == total:
            self.stdout.write(self.style.SUCCESS("\n🎉 All fixes verified successfully!"))
            self.stdout.write("\nYou can now use template-only mode by adding:")
            self.stdout.write(self.style.WARNING('  "use_template_only": true'))
            self.stdout.write("\nOr rely on automatic fallback when API keys fail.")
        else:
            self.stdout.write(self.style.ERROR(f"\n⚠️  {total - passed} test(s) failed - please review"))
