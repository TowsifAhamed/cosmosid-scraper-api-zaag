from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from .serializers import UserRegistrationSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import status, permissions
from django.contrib.auth import authenticate
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.contrib.auth.models import User

class UserRegistrationView(APIView):
    """
    View to register a new user.
    """
    @swagger_auto_schema(
        request_body=UserRegistrationSerializer,
        responses={
            201: "User created successfully",
            400: "Invalid input"
        }
    )
    def post(self, request):
        """
        Register a new user.
        """
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()

            # Generate tokens for the user
            refresh = RefreshToken.for_user(user)
            
            response_data = {
                "message": "User created successfully",
                "data": serializer.data,
                "token": str(refresh.access_token)
            }
            return Response(response_data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CustomLoginView(APIView):
    """
    View to log a user in and provide JWT tokens along with user details.
    """
    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'username': openapi.Schema(type=openapi.TYPE_STRING, description='Username'),
                'password': openapi.Schema(type=openapi.TYPE_STRING, description='Password'),
            }
        ),
        responses={
            200: openapi.Response(
                description="Tokens returned along with user data",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'data': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            description="User details"
                        ),
                        'token': openapi.Schema(type=openapi.TYPE_STRING),
                        'refreshToken': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            ),
            401: "Invalid credentials"
        }
    )
    def post(self, request):
        """
        Log in a user and return JWT tokens along with user details.
        """
        username = request.data.get('username')
        password = request.data.get('password')
        
        # Authenticate the user
        user = authenticate(username=username, password=password)
        
        if user is not None:
            # Generate tokens
            refresh = RefreshToken.for_user(user)
            
            response_data = {
                "data": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name
                },
                "token": str(refresh.access_token),
                "refreshToken": str(refresh)
            }
            return Response(response_data, status=status.HTTP_200_OK)
        
        return Response({'detail': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

class LogoutView(APIView):
    """
    View to log a user out by blacklisting the refresh token.
    """
    permission_classes = (permissions.IsAuthenticated,)

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'refresh_token': openapi.Schema(type=openapi.TYPE_STRING, description='Refresh token to be blacklisted'),
            }
        ),
        responses={
            205: "Token blacklisted successfully",
            400: "Bad request"
        }
    )
    def post(self, request):
        """
        Log out a user by blacklisting the refresh token.
        """
        try:
            refresh_token = request.data["refresh_token"]
            token = RefreshToken(refresh_token)
            token.blacklist()  # Blacklist the token to ensure it's no longer valid
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response(status=status.HTTP_400_BAD_REQUEST)
