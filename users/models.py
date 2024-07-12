from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone



# Custom user manager for users_customers
class CustomUserManager(BaseUserManager):
    def create_user(self, username, email, password=None, **extra_fields):
        if not username:
            raise ValueError('The Username field must be set')
        if not email:
            raise ValueError('The Email field must be set')

        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(username, email, password, **extra_fields)


# CustomUser model for users_customers
class CustomUser(AbstractBaseUser, PermissionsMixin):
    id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    password = models.CharField(max_length=255)
    last_login = models.DateTimeField(null=True, blank=True)
    is_superuser = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(auto_now_add=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    class Meta:
        db_table = 'users_customuser'

    def __str__(self):
        return self.username


# Model for internal user management in the 'users' table
class InternalUser(models.Model):
    UserCode = models.CharField(max_length=50, primary_key=True)
    UserName = models.CharField(max_length=100)
    PhoneNumber = models.CharField(max_length=15, null=True, blank=True)
    Grouping = models.CharField(max_length=50, null=True, blank=True)
    IsBlocked = models.BooleanField(default=False)
    LoginName = models.CharField(max_length=100)
    AreaCode = models.CharField(max_length=10, null=True, blank=True)
    CityID = models.IntegerField(null=True, blank=True)
    RouteCode = models.CharField(max_length=10, null=True, blank=True)
    ParentCode = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        db_table = 'users'

    def __str__(self):
        return self.UserName


class Regions(models.Model):
    Region_Code = models.CharField(max_length=50, primary_key=True)
    Org_ID = models.CharField(max_length=50)
    Region_Description = models.CharField(max_length=100)
    Region_Alt_Description = models.CharField(max_length=100)
    Stamp_Date = models.DateTimeField()

    def __str__(self):
        return self.Region_Description


class Parameters(models.Model):
    ParameterName = models.CharField(max_length=100)
    DefaultValue = models.CharField(max_length=100)
    ParameterType = models.CharField(max_length=50)

    class Meta:
        db_table = 'User_Parameters'

    def __str__(self):
        return self.ParameterName
class Routes(models.Model):
    Route_ID = models.AutoField(primary_key=True)
    Branch_Code = models.CharField(max_length=50)
    Route_Description = models.CharField(max_length=100)
    Route_Alt_Description = models.CharField(max_length=100)
    Region_Code = models.CharField(max_length=50)
    Stamp_Date = models.DateTimeField()

    class Meta:
        db_table = 'Routes'

class Route_Users(models.Model):
    Route_ID = models.ForeignKey('Routes', on_delete=models.CASCADE)
    User_Code = models.ForeignKey('users.InternalUser', on_delete=models.CASCADE)
    Stamp_Date = models.DateTimeField()
    Assignment_Type = models.IntegerField()
    class Meta:
        db_table = 'Route_Users'
        unique_together = ('Route_ID', 'User_Code')


class Clients(models.Model):
    Client_Code = models.TextField(primary_key=True)
    Org_ID = models.TextField()
    Channel_Code = models.TextField(null=True, blank=True)
    Area_Of_Business_Code = models.TextField(null=True, blank=True)
    Region_Code = models.TextField(null=True, blank=True)
    City_Code = models.TextField(null=True, blank=True)
    Area_Code = models.TextField(null=True, blank=True)
    Client_Description = models.TextField(null=True, blank=True)
    Client_Alt_Description = models.TextField(null=True, blank=True)
    Payment_Term_Code = models.TextField(null=True, blank=True)
    Email = models.TextField(null=True, blank=True)
    Address = models.TextField(null=True, blank=True)
    Alt_Address = models.TextField(null=True, blank=True)
    Contact_Person = models.TextField(null=True, blank=True)
    Is_Dummy = models.BooleanField(default=False)
    Phone_Number = models.TextField(null=True, blank=True)
    Fax_Number = models.TextField(null=True, blank=True)
    Longitude = models.TextField(null=True, blank=True)
    Latitude = models.TextField(null=True, blank=True)
    Tax_Code = models.TextField(null=True, blank=True)
    Barcode = models.TextField(null=True, blank=True)
    IsFromERP = models.BooleanField(default=False)
    Client_Status_ID = models.IntegerField(null=True, blank=True)
    Currency_Code = models.TextField(null=True, blank=True)
    Sq_Meter_Area = models.TextField(null=True, blank=True)
    Collection_Type = models.IntegerField(null=True, blank=True)
    Client_Type_ID = models.IntegerField(null=True, blank=True)
    Stamp_Date = models.DateTimeField()
    User_Code = models.TextField(null=True, blank=True)
    Parent_Client_Code = models.TextField(null=True, blank=True)
    Price_List_Code = models.TextField(null=True, blank=True)
    Is_From_Census = models.BooleanField(default=False)
    Price_List_Code2 = models.TextField(null=True, blank=True)
    Return_Price_List_Code = models.TextField(null=True, blank=True)
    Grace_Period = models.IntegerField(null=True, blank=True)
    Is_Taxable = models.BooleanField(default=False)
    Invoice_Limit = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)
    Invoice_Settlement = models.IntegerField(null=True, blank=True)
    Allow_PDC = models.BooleanField(default=False)
    Allow_Check = models.BooleanField(default=False)
    Number_Of_Outlets = models.IntegerField(null=True, blank=True)
    Classification_Code = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'Clients'
        managed = False  # Set to False because Django should not manage this table

    def __str__(self):
        return self.Client_Description

class PromoHeaders(models.Model):
        promotion_id = models.AutoField(primary_key=True)
        promotion_type = models.CharField(max_length=3)
        start_date = models.DateTimeField()
        end_date = models.DateTimeField()
        promotion_description = models.CharField(max_length=100)
        achievement = models.DecimalField(max_digits=18, decimal_places=6)
        target_value = models.DecimalField(max_digits=18, decimal_places=6)
        is_active = models.BooleanField(default=False)
        is_forced = models.BooleanField(default=False)
        parent_id = models.CharField(max_length=14, null=True, blank=True)
        priority = models.IntegerField()
        promotion_apply = models.IntegerField()

        def __str__(self):
            return f'{self.promotion_description} ({self.promotion_id})'

        class Meta:
            db_table = 'Promo_Headers'


class PromoAssignments(models.Model):
    org_id = models.IntegerField()
    assignment_code = models.CharField(max_length=50, primary_key=True)
    assignment_type = models.CharField(max_length=50)
    second_assignment_type = models.CharField(max_length=50)
    second_assignment_code = models.CharField(max_length=50)
    stamp_date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.assignment_code

class PromoItemBasketHeaders(models.Model):
    item_basket_id = models.AutoField(primary_key=True)
    item_basket_description = models.CharField(max_length=100)
    creation_date = models.DateTimeField(default=timezone.now)
    last_updated_date = models.DateTimeField()

    class Meta:
        db_table = 'Promo_Item_Basket_Headers'

    def __str__(self):
        return self.item_basket_description
