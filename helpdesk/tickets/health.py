"""
Health check endpoint for monitoring.
Add this to your URLs for uptime monitoring.
"""
from django.http import JsonResponse
from django.views import View
from django.db import connection
from django.core.cache import cache


class HealthCheckView(View):
    """Health check endpoint for monitoring."""
    
    def get(self, request):
        """Check database, cache, and overall health."""
        health_data = {
            'status': 'healthy',
            'timestamp': None,
            'checks': {}
        }
        
        try:
            import datetime
            health_data['timestamp'] = datetime.datetime.now().isoformat()
            
            # Database check
            try:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    health_data['checks']['database'] = 'ok'
            except Exception as e:
                health_data['checks']['database'] = f'error: {str(e)}'
                health_data['status'] = 'unhealthy'
            
            # Cache check
            try:
                cache.set('health_check', 'test', 5)
                if cache.get('health_check') == 'test':
                    health_data['checks']['cache'] = 'ok'
                else:
                    health_data['checks']['cache'] = 'error: cache not working'
                    health_data['status'] = 'unhealthy'
            except Exception as e:
                health_data['checks']['cache'] = f'error: {str(e)}'
                health_data['status'] = 'unhealthy'
            
            # Application check
            health_data['checks']['application'] = 'ok'
            
        except Exception as e:
            health_data['status'] = 'error'
            health_data['message'] = f'Health check failed: {str(e)}'
        
        return JsonResponse(health_data, status=200 if health_data['status'] == 'healthy' else 503)