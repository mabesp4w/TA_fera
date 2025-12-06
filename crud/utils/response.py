# utils/response.py
from rest_framework.response import Response
from rest_framework import status


class APIResponse:
    """Utility class untuk format response yang konsisten"""

    @staticmethod
    def success(data=None, message="Success", status_code=status.HTTP_200_OK):
        """Response untuk sukses"""
        return Response({
            'status': 'success',
            'message': message,
            'results': data
        }, status=status_code)

    @staticmethod
    def error(message="Error", errors=None, status_code=status.HTTP_400_BAD_REQUEST):
        """Response untuk error"""
        response_data = {
            'status': 'error',
            'message': message,
        }
        if errors:
            response_data['errors'] = errors
        return Response(response_data, status=status_code)

    @staticmethod
    def paginated_success(data, message="Success", pagination_data=None):
        """Response untuk data yang dipaginasi"""
        result = {
            'data': data,
        }
        if pagination_data:
            result.update(pagination_data)

        return Response({
            'status': 'success',
            'message': message,
            'results': result
        }, status=status.HTTP_200_OK)