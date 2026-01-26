from django.http import JsonResponse

def workflow_list(request):
    return JsonResponse({'workflows': []})
