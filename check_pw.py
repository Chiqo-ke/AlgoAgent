import os, sys
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "algoagent_api.settings")
sys.path.insert(0, r"C:\Users\nyaga\Documents\AlgoAgent\monolithic_agent")

import django
django.setup()

from django.contrib.auth import get_user_model, authenticate
U = get_user_model()

try:
    u = U.objects.get(username="algotrader")
    print("User found:", u.username, "email:", u.email)
    print("check Trading@2024:", u.check_password("Trading@2024"))
    print("check algotrader123:", u.check_password("algotrader123"))
    print("check Algotrader123:", u.check_password("Algotrader123"))
    print("check Trading2024:", u.check_password("Trading2024"))
    print("check trading@2024:", u.check_password("trading@2024"))
    # Force reset to known value
    u.set_password("LiveTest@2026")
    u.save()
    print("Password RESET to: LiveTest@2026")
except U.DoesNotExist:
    print("ERROR: algotrader user does not exist")
    for usr in U.objects.all():
        print(" -", usr.username, usr.email, usr.is_active)
