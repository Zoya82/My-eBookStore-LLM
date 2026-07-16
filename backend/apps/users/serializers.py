from rest_framework import serializers
from .models import User, Address

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id','username','phone','avatar','gender','email','is_active','is_staff','is_superuser']
        read_only_fields = ['id','phone','is_active','is_staff','is_superuser']
    def validate(self, attrs):
        forbidden = set(self.initial_data) - {'username','avatar','gender','email'}
        if forbidden:
            raise serializers.ValidationError({f: '该字段不可修改' for f in sorted(forbidden)})
        return attrs
    def validate_username(self, value):
        value = value.strip()
        if not 3 <= len(value) <= 150:
            raise serializers.ValidationError('用户名长度必须为3-150个字符且不能为空')
        qs = User.objects.filter(username=value)
        if self.instance: qs = qs.exclude(pk=self.instance.pk)
        if qs.exists(): raise serializers.ValidationError('用户名已存在')
        return value
    def validate_gender(self, value):
        if value not in ('M','F',None,''): raise serializers.ValidationError('gender 只能为 M、F 或空值')
        return value or None

class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(required=True, min_length=3, max_length=150, trim_whitespace=True)
    phone = serializers.CharField(required=True)
    password = serializers.CharField(required=True, min_length=6, max_length=128, write_only=True)
    def validate_username(self, value):
        value = value.strip()
        if not value: raise serializers.ValidationError('用户名不能为空')
        if User.objects.filter(username=value).exists(): raise serializers.ValidationError('用户名已存在')
        return value
    def validate_phone(self, value):
        if len(value) != 11 or not value.isdigit(): raise serializers.ValidationError('手机号必须为11位数字')
        if User.objects.filter(phone=value).exists(): raise serializers.ValidationError('手机号已存在')
        return value

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True, max_length=150)
    password = serializers.CharField(required=True, max_length=128, write_only=True)

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True, write_only=True, max_length=128)
    new_password = serializers.CharField(required=True, write_only=True, min_length=6, max_length=128)
    confirm_password = serializers.CharField(required=True, write_only=True, max_length=128)
    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']: raise serializers.ValidationError({'confirm_password': ['两次新密码不一致']})
        return attrs

class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ['id','receiver','phone','province','city','district','detail','is_default']
        read_only_fields = ['user']
    def validate(self, attrs):
        for field in ('receiver','province','city','district','detail'):
            if field in attrs:
                attrs[field] = attrs[field].strip()
                if not attrs[field]: raise serializers.ValidationError({field: '该字段不能为空'})
        phone = attrs.get('phone')
        if phone is not None and (len(phone) != 11 or not phone.isdigit()): raise serializers.ValidationError({'phone': '手机号必须为11位数字'})
        return attrs
