import json

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.db import connection
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from .models import InternalUser, CustomUser, Routes, Clients,PromoItemBasketHeaders,PromoHeaders
from .forms import PromotionSearchForm, NewPromotionForm, UserForm, AssignPromotionSearchForm, BasketForm
from django.views.decorators.http import require_GET
from django.db import connection, DatabaseError
from django.utils import timezone  # To get the current date and time

from django.shortcuts import render, redirect
from django.db import connection
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from django.core import serializers

from django.http import JsonResponse
from django.db import connection, transaction


import logging

logger = logging.getLogger(__name__)

def home(request):
    return render(request, 'home/home.html')

@login_required
def edit_route(request, route_id):
    if request.method == 'POST':
        route_description = request.POST.get('route_description')
        region_code = request.POST.get('region_description')

        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE Routes
                SET Route_Description = %s, Region_Code = %s
                WHERE Route_ID = %s
            """, [route_description, region_code, route_id])

        messages.success(request, 'Route updated successfully.')
        return redirect('routes')



@login_required
def edit_user(request, user_code):
    if request.method == 'POST':
        # Get the data from the form
        user_name = request.POST.get('user_name')
        phone_number = request.POST.get('phone_number')
        grouping = request.POST.get('grouping')
        is_blocked = request.POST.get('is_blocked')
        login_name = request.POST.get('login_name')
        area_code = request.POST.get('area_code')
        city_id = request.POST.get('city_id')
        route_code = request.POST.get('route_code')
        parent_code = request.POST.get('parent_code')

        try:
            with connection.cursor() as cursor:
                # Execute the update query
                cursor.execute("""
                    UPDATE users
                    SET UserName = %s,
                        PhoneNumber = %s,
                        Grouping = %s,
                        IsBlocked = %s,
                        LoginName = %s,
                        AreaCode = %s,
                        CityID = %s,
                        RouteCode = %s,
                        ParentCode = %s
                    WHERE UserCode = %s
                """, [
                    user_name, phone_number, grouping, is_blocked,
                    login_name, area_code, city_id, route_code,
                    parent_code, user_code
                ])

            # If no exceptions were raised, display a success message
            messages.success(request, 'User updated successfully.')
        except Exception as e:
            # Log the error if needed and display an error message
            messages.error(request, f'Error updating user: {str(e)}')

        # Redirect to the users list page
        return redirect('users')

    # If not a POST request, render the form with the current user data
    else:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT UserName, PhoneNumber, Grouping, IsBlocked, LoginName, AreaCode, CityID, RouteCode, ParentCode
                FROM users
                WHERE UserCode = %s
            """, [user_code])
            user = cursor.fetchone()

        # Check if user exists
        if not user:
            messages.error(request, 'User not found.')
            return redirect('users')

        # Prepare the user data to render the form
        user_data = {
            'user_code': user_code,
            'user_name': user[0],
            'phone_number': user[1],
            'grouping': user[2],
            'is_blocked': user[3],
            'login_name': user[4],
            'area_code': user[5],
            'city_id': user[6],
            'route_code': user[7],
            'parent_code': user[8],
        }

        return render(request, 'users/edit_user.html', {'user': user_data})


def users(request):
    # Fetch parameters data
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM Parameters")
        parameters_data = cursor.fetchall()

    parameters_list = [{'ParameterName': row[1], 'ParameterType': row[3], 'DefaultValue': row[2]} for row in
                       parameters_data]

    # Extract query parameters from the request
    user_code = request.GET.get('user_code', '').strip()
    user_name = request.GET.get('user_name', '').strip()
    phone_number = request.GET.get('phone_number', '').strip()
    type_user = request.GET.get('type_user', '').strip()

    # Initialize base query and parameters list
    query = """
        SELECT UserCode, UserName, PhoneNumber, ug.Grouping, IsBlocked,
               LoginName, AreaCode, CityID, RouteCode, ParentCode
        FROM users u
        LEFT JOIN User_Groups ug ON u.Grouping = ug.Grouping
        WHERE 1=1
    """

    params = []

    # Add conditions to the query based on the provided parameters
    if user_code:
        query += " AND UserCode LIKE %s"
        params.append(f"%{user_code}%")

    if user_name:
        query += " AND UserName LIKE %s"
        params.append(f"%{user_name}%")

    if phone_number:
        query += " AND PhoneNumber LIKE %s"
        params.append(f"%{phone_number}%")

    if type_user:
        query += " AND Grouping = %s"
        params.append(type_user)

    # Execute the query with the accumulated parameters
    with connection.cursor() as cursor:
        cursor.execute(query, params)
        users_data = cursor.fetchall()

    # Prepare the users list
    users_list = [{
        'UserCode': row[0],
        'UserName': row[1],
        'PhoneNumber': row[2],
        'Grouping': row[3],
        'IsBlocked': row[4],
        'LoginName': row[5],
        'AreaCode': row[6],
        'CityID': row[7],
        'RouteCode': row[8],
        'ParentCode': row[9],
    } for row in users_data]

    # Render the template with the filtered users and parameters
    return render(request, 'users/home.html', {'users': users_list, 'parameters': parameters_list})



def user_parameters(request, user_code):
    try:
        print(f"Fetching parameters for user code: {user_code}")

        # Query to fetch all parameters with default values
        sql_query_all_params = """
            SELECT ID, ParameterName, DefaultValue
            FROM Parameters
        """

        with connection.cursor() as cursor:
            cursor.execute(sql_query_all_params)
            all_parameters_data = cursor.fetchall()

        # Create a dictionary for all parameters with default values
        all_parameters = {row[1]: {'ParameterName': row[1], 'ParameterValue': row[2], 'DefaultValue': row[2]} for row in all_parameters_data}

        # Query to fetch user-specific parameters
        sql_query_user_params = """
            SELECT up.ParameterName, up.ParameterValue
            FROM User_Parameters up
            WHERE up.UserCode = %s
        """

        with connection.cursor() as cursor:
            cursor.execute(sql_query_user_params, [user_code])
            user_parameters_data = cursor.fetchall()

        # Update the parameters with user-specific values
        for param_name, param_value in user_parameters_data:
            if param_name in all_parameters:
                all_parameters[param_name]['ParameterValue'] = param_value

        # Convert dictionary back to list for JSON response
        user_parameters = list(all_parameters.values())

        return JsonResponse(user_parameters, safe=False)
    except Exception as e:
        print(f"Error fetching user parameters: {e}")
        return JsonResponse({'error': str(e)}, status=500)
def user_parameters(request, user_code):
    try:
        # Query to fetch all parameters with default values
        sql_query_all_params = """
            SELECT ID, ParameterName, DefaultValue
            FROM Parameters
        """

        with connection.cursor() as cursor:
            cursor.execute(sql_query_all_params)
            all_parameters_data = cursor.fetchall()

        # Create a dictionary for all parameters with default values
        all_parameters = {row[1]: {'ParameterName': row[1], 'ParameterValue': row[2], 'DefaultValue': row[2]} for row in all_parameters_data}

        # Query to fetch user-specific parameters
        sql_query_user_params = """
            SELECT up.ParameterName, up.ParameterValue
            FROM User_Parameters up
            WHERE up.UserCode = %s
        """

        with connection.cursor() as cursor:
            cursor.execute(sql_query_user_params, [user_code])
            user_parameters_data = cursor.fetchall()

        # Update the parameters with user-specific values
        for param_name, param_value in user_parameters_data:
            if param_name in all_parameters:
                all_parameters[param_name]['ParameterValue'] = param_value

        # Convert dictionary back to list for JSON response
        user_parameters = list(all_parameters.values())

        return JsonResponse(user_parameters, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# View to save user details
@csrf_exempt
def save_user(request):
    if request.method == 'POST':
        user_code = request.POST.get('UserCode')
        user_name = request.POST.get('UserName')
        phone_number = request.POST.get('PhoneNumber')
        grouping = request.POST.get('Grouping')
        is_blocked = request.POST.get('IsBlocked')
        login_name = request.POST.get('LoginName')
        area_code = request.POST.get('AreaCode')
        city_id = request.POST.get('CityID')
        route_code = request.POST.get('RouteCode')
        parent_code = request.POST.get('ParentCode')

        user, created = InternalUser.objects.update_or_create(
            UserCode=user_code,
            defaults={
                'UserName': user_name,
                'PhoneNumber': phone_number,
                'Grouping': grouping,
                'IsBlocked': is_blocked,
                'LoginName': login_name,
                'AreaCode': area_code,
                'CityID': city_id,
                'RouteCode': route_code,
                'ParentCode': parent_code,
            }
        )

        return JsonResponse({'status': 'success', 'created': created})

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)


# User login view for customers (authentication)
def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Invalid username or password.')

    return render(request, 'login.html')


# User logout view
def user_logout(request):
    logout(request)
    return redirect('home')


def promotions(request):
    form = PromotionSearchForm(request.GET or None)
    params = {}
    query = """
        SELECT 
            Promotion_ID, 
            Promotion_Description, 
            Promotion_Type, 
            Start_Date, 
            End_Date, 
            Is_Forced, 
            Is_Active, 
            Priority, 
            Promotion_Apply
        FROM 
            Promo_Headers
        WHERE 1=1
    """

    if request.GET:
        if form.is_valid():
            promotion_id = form.cleaned_data.get('promotion_id')
            promotion_description = form.cleaned_data.get('promotion_description')
            start_date = form.cleaned_data.get('start_date')
            end_date = form.cleaned_data.get('end_date')

            if promotion_id:
                query += " AND Promotion_ID = %(promotion_id)s"
                params['promotion_id'] = promotion_id

            if promotion_description:
                query += " AND Promotion_Description LIKE %(promotion_description)s"
                params['promotion_description'] = f"%{promotion_description}%"

            if start_date:
                query += " AND Start_Date >= %(start_date)s"
                params['start_date'] = start_date

            if end_date:
                query += " AND End_Date <= %(end_date)s"
                params['end_date'] = end_date

    with connection.cursor() as cursor:
        cursor.execute(query, params)
        columns = [col[0] for col in cursor.description]
        promotions = [dict(zip(columns, row)) for row in cursor.fetchall()]

    context = {
        'form': form,
        'promotions': promotions
    }

    return render(request, 'promotions/home.html', context)
def create_promotion(request):
    if request.method == 'POST':
        form = NewPromotionForm(request.POST)
        if form.is_valid():
            promotion_description = form.cleaned_data['promotion_description']
            start_date = form.cleaned_data['start_date']
            end_date = form.cleaned_data['end_date']
            priority = form.cleaned_data['priority']
            max_applied = form.cleaned_data['max_applied']
            is_active = form.cleaned_data['is_active']
            is_forced = form.cleaned_data['is_forced']
            promotion_type = form.cleaned_data['promotion_type']
            promotion_apply = form.cleaned_data['promotion_apply']

            query = """
                INSERT INTO Promo_Headers (
                    Promotion_Description,
                    Start_Date,
                    End_Date,
                    Priority,
                    Is_Active,
                    Is_Forced,
                    Promotion_Type,
                    Promotion_Apply
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            params = [
                promotion_description,
                start_date,
                end_date,
                priority,
                is_active,
                is_forced,
                promotion_type,
                promotion_apply
            ]
            with connection.cursor() as cursor:
                cursor.execute(query, params)
                return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'error': form.errors})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})


from django.http import JsonResponse
from django.shortcuts import render
from django.db import connection

def assign_promotions(request):
    form = AssignPromotionSearchForm(request.GET or None)
    params = {}
    query = """
        SELECT 
            Promotion_ID, 
            Promotion_Description, 
            Start_Date, 
            End_Date
        FROM 
            Promo_Headers
        WHERE 1=1
    """

    if request.GET:
        if form.is_valid():
            promotion_type = form.cleaned_data.get('promotion_type')
            search_date = form.cleaned_data.get('search_date')

            if promotion_type:
                query += " AND Promotion_Type = %(promotion_type)s"
                params['promotion_type'] = promotion_type

            if search_date:
                query += " AND %(search_date)s BETWEEN Start_Date AND End_Date"
                params['search_date'] = search_date

    with connection.cursor() as cursor:
        cursor.execute(query, params)
        columns = [col[0] for col in cursor.description]
        promotions = [dict(zip(columns, row)) for row in cursor.fetchall()]

    context = {
        'form': form,
        'promotions': promotions,
    }
    return render(request, 'promotions/assign_promotions.html', context)

def load_entities(request):
    promotion_id = request.GET.get('promotion_id')
    filter_type = request.GET.get('filter_type')
    available_entities = []
    assigned_entities = []

    if filter_type == 'users':
        available_query = """
            SELECT UserCode, UserName
            FROM Users
            WHERE UserCode NOT IN (
                SELECT UserCode
                FROM Promo_Assignments
                WHERE Promotion_ID = %s
            )
        """
        assigned_query = """
            SELECT u.UserCode, u.UserName
            FROM Users u
            JOIN Promo_Assignments up ON u.UserCode = up.UserCode
            WHERE up.Promotion_ID = %s
        """
    elif filter_type == 'clients':
        available_query = """
            SELECT Client_Code, Client_Description
            FROM Clients
            WHERE Client_Code NOT IN (
                SELECT Client_Code
                FROM Promo_Assignments
                WHERE Promotion_ID = %s
            )
        """
        assigned_query = """
            SELECT c.Client_Code, c.Client_Description
            FROM Clients c
            JOIN Promo_Assignments cp ON c.Client_Code = cp.Client_Code
            WHERE cp.Promotion_ID = %s
        """

    with connection.cursor() as cursor:
        cursor.execute(available_query, [promotion_id])
        available_entities = cursor.fetchall()

        cursor.execute(assigned_query, [promotion_id])
        assigned_entities = cursor.fetchall()

    available_html = ""
    assigned_html = ""

    if filter_type == 'users':
        available_html += """
            <tr>
                <th>User Code</th>
                <th>User Name</th>
            </tr>
        """
        assigned_html += """
            <tr>
                <th>User Code</th>
                <th>User Name</th>
            </tr>
        """
    elif filter_type == 'clients':
        available_html += """
            <tr>
                <th>Client Code</th>
                <th>Client Description</th>
            </tr>
        """
        assigned_html += """
            <tr>
                <th>Client Code</th>
                <th>Client Description</th>
            </tr>
        """

    for entity in available_entities:
        available_html += f"<tr><td>{entity[0]}</td><td>{entity[1]}</td></tr>"

    for entity in assigned_entities:
        assigned_html += f"<tr><td>{entity[0]}</td><td>{entity[1]}</td></tr>"

    return JsonResponse({
        'available': available_html,
        'assigned': assigned_html
    })

@csrf_exempt
def assign_entity(request):
    if request.method == 'POST':
        try:
            entity_id = request.POST.get('entity_id')
            promotion_id = request.POST.get('promotion_id')
            filter_type = request.POST.get('filter_type')
            action = request.POST.get('action')

            if not entity_id or not promotion_id or not filter_type or not action:
                return JsonResponse({'error': 'Missing parameters'}, status=400)

            with connection.cursor() as cursor:
                if filter_type == 'users' and action == 'assign':
                    cursor.execute("""
                        INSERT INTO Promo_Assignments (Promotion_ID, UserCode)
                        VALUES (%s, %s)
                    """, [promotion_id, entity_id])
                elif filter_type == 'users' and action == 'unassign':
                    cursor.execute("""
                        DELETE FROM Promo_Assignments 
                        WHERE Promotion_ID = %s AND UserCode = %s
                    """, [promotion_id, entity_id])
                elif filter_type == 'clients' and action == 'assign':
                    cursor.execute("""
                        INSERT INTO Promo_Assignments (Promotion_ID, Client_Code)
                        VALUES (%s, %s)
                    """, [promotion_id, entity_id])
                elif filter_type == 'clients' and action == 'unassign':
                    cursor.execute("""
                        DELETE FROM Promo_Assignments 
                        WHERE Promotion_ID = %s AND Client_Code = %s
                    """, [promotion_id, entity_id])
                else:
                    return JsonResponse({'error': 'Invalid action or filter type'}, status=400)

            return JsonResponse({'success': True})
        except Exception as e:
            logger.error(f"Error assigning entity: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request method'}, status=405)

def define_basket(request):
    baskets = PromoItemBasketHeaders.objects.all()
    form = BasketForm()  # Assuming you have a form defined for adding new baskets

    context = {
        'baskets': baskets,
        'form': form,
    }
    return render(request, 'promotions/define_basket.html', context)


def add_basket(request):
    if request.method == 'POST':
        form = BasketForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('define_basket')  # Redirect back to the define_basket page after adding
    else:
        form = BasketForm()


# views.py

def get_basket(request, item_basket_id=None):
    if item_basket_id is None:
        return JsonResponse({'success': False, 'error': 'No basket ID provided'}, status=400)

    query = """
            SELECT * 
            FROM Promo_Item_Basket_Headers 
    
        """
    with connection.cursor() as cursor:
        cursor.execute(query, [item_basket_id])
        row = cursor.fetchone()

    if row:
        basket = {
            'item_basket_id': row[0],
            'item_basket_description': row[1]  # Use the correct index
        }
        return JsonResponse({'success': True, 'basket': basket})
    else:
        return JsonResponse({'success': False, 'error': 'Basket not found'}, status=404)

def get_promotion(request, promotion_id):
    query = """
        SELECT * FROM Promo_Headers WHERE Promotion_ID = %s
    """
    with connection.cursor() as cursor:
        cursor.execute(query, [promotion_id])
        row = cursor.fetchone()

    if row:
        promotion = {
            'Promotion_ID': row[1],
            'Promotion_Description': row[5],
            'Promotion_Type': row[2],
            'Start_Date': row[3],
            'End_Date': row[4],
            'Is_Forced': row[8],
            'Is_Active': row[9],
            'Priority': row[13],
            'Promotion_Apply': row[14]
            # Include all fields
        }
        return JsonResponse({'success': True, 'promotion': promotion})
    else:
        return JsonResponse({'success': False, 'error': 'Promotion not found'})

# View for editing a promotion
def edit_promotion(request):
    if request.method == 'POST':
        promotion_id = request.POST.get('promotion_id')
        promotion_description = request.POST.get('promotion_description')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        priority = request.POST.get('priority')
        is_active = request.POST.get('is_active')
        is_forced = request.POST.get('is_forced')
        promotion_type = request.POST.get('promotion_type')
        promotion_apply = request.POST.get('promotion_apply')

        query = """
            UPDATE Promo_Headers
            SET Promotion_Description = %s,
                Start_Date = %s,
                End_Date = %s,
                Priority = %s,
                Is_Active = %s,
                Is_Forced = %s,
                Promotion_Type = %s,
                Promotion_Apply = %s
            WHERE Promotion_ID = %s
        """
        params = [
            promotion_description,
            start_date,
            end_date,
            priority,
            is_active,
            is_forced,
            promotion_type,
            promotion_apply,
            promotion_id
        ]
        with connection.cursor() as cursor:
            cursor.execute(query, params)
            return JsonResponse({'success': True})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})

# View for deleting a promotion
def delete_promotion(request):
    if request.method == 'POST':
        promotion_id = request.POST.get('promotion_id')

        query = """
            DELETE FROM Promo_Headers WHERE Promotion_ID = %s
        """
        with connection.cursor() as cursor:
            cursor.execute(query, [promotion_id])
            return JsonResponse({'success': True})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@require_GET
def search_baskets(request):
    query = request.GET.get('query', '')
    baskets = PromoItemBasketHeaders.objects.filter(item_basket_description__icontains=query)
    basket_data = [{'item_basket_id': basket.item_basket_id, 'item_basket_description': basket.item_basket_description} for basket in baskets]
    return JsonResponse({'success': True, 'results': basket_data})


@csrf_exempt
def update_checkbox(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            promotion_id = data.get('promotion_id')
            field = data.get('field')
            value = data.get('value')

            # Use raw SQL to update the database
            with connection.cursor() as cursor:
                cursor.execute(
                    f"UPDATE Promo_Headers SET {field} = %s WHERE Promotion_ID = %s",
                    [value, promotion_id]
                )

            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})
def get_regions():
    with connection.cursor() as cursor:
        cursor.execute("SELECT Region_Code, Region_Description FROM Regions")
        rows = cursor.fetchall()
    regions = [{'Region_Code': row[0], 'Region_Description': row[1]} for row in rows]
    return regions

def routes(request):
    current_user = request.user
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT r.Route_ID, r.Route_Description, r.Region_Code, rg.Region_Description
            FROM Routes r
            LEFT JOIN Regions rg ON r.Region_Code = rg.Region_Code
        """)
        routes_data = cursor.fetchall()
    routes_list = [{
        'Route_ID': row[0],
        'Route_Description': row[1],
        'Region_Code': row[2],
        'Region_Description': row[3],
        #'CreateBy': current_user.username,
        'HasClients': False
    } for row in routes_data]
    regions = get_regions()
    return render(request, 'routes/home.html', {'routes': routes_list, 'regions': regions})

@login_required
def add_route(request):
    if request.method == 'POST':
        route_description = request.POST.get('route_description')
        region_code = request.POST.get('region_description')
        create_by = request.user.username

        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO Routes (Route_Description, Region_Code, CreateBy)
                VALUES (%s, %s, %s)
            """, [route_description, region_code, create_by])

        messages.success(request, 'Route added successfully.')
        return redirect('routes')

    regions = get_regions()
    return render(request, 'routes/home.html', {'regions': regions})


@login_required
def delete_route(request, route_id):
    with connection.cursor() as cursor:
        cursor.execute("""
            DELETE FROM Routes
            WHERE Route_ID = %s
        """, [route_id])

    messages.success(request, 'Route deleted successfully.')
    return redirect('routes')

def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'authentication/login.html')

def user_logout(request):
    logout(request)
    return redirect('home')

def list_users(request):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT UserCode, UserName, PhoneNumber, Grouping, IsBlocked,
                   LoginName, AreaCode, CityID, RouteCode, ParentCode
            FROM users
        """)
        users_data = cursor.fetchall()

    users_list = []
    for row in users_data:
        user = {
            'UserCode': row[0],
            'UserName': row[1],
            'PhoneNumber': row[2],
            'Grouping': row[3],
            'IsBlocked': row[4],
            'LoginName': row[5],
            'AreaCode': row[6],
            'CityID': row[7],
            'RouteCode': row[8],
            'ParentCode': row[9],
        }
        users_list.append(user)

    return render(request, 'list_users.html', {'users': users_list})

def fetch_users():
    with connection.cursor() as cursor:
        cursor.execute("SELECT UserCode, UserName FROM Users")
        rows = cursor.fetchall()
    users = [{'UserCode': row[0], 'UserName': row[1]} for row in rows]
    return users
def get_users(request):
    users = InternalUser.objects.all().values('UserCode', 'UserName')
    return JsonResponse({'users': list(users)})




def affectation_clients_routes(request):
    if request.method == 'GET' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        action = request.GET.get('action')
        if action == 'get_routes':
            try:
                routes = Routes.objects.all().values('Route_ID', 'Route_Description')
                return JsonResponse({'routes': list(routes)}, safe=False)
            except Exception as e:
                logger.error(f"Error fetching routes: {str(e)}")
                return JsonResponse({'error': 'An error occurred while fetching routes. Please try again later.'}, status=500)
        elif action == 'get_route_clients':
            route_id = request.GET.get('route_id')
            if not route_id:
                return JsonResponse({'error': 'No route ID provided'}, status=400)
            try:
                assigned_clients = Clients.objects.filter(route_id=route_id).values('Client_Code', 'Client_Description')
                available_clients = Clients.objects.filter(route_id__isnull=True).values('Client_Code', 'Client_Description')
                return JsonResponse({'assigned_clients': list(assigned_clients), 'available_clients': list(available_clients)})
            except Exception as e:
                logger.error(f"Error fetching route clients for route_id {route_id}: {str(e)}")
                return JsonResponse({'error': 'An error occurred while fetching route clients. Please try again later.'}, status=500)
    return render(request, 'routes/affectation_clients_routes.html')


def get_routes(request):
    try:
        routes = Routes.objects.all().values('Route_ID', 'Route_Description')
        return JsonResponse({'routes': list(routes)})
    except Exception as e:
        logger.error(f"Error fetching routes: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

def get_route_clients(request):
    route_id = request.GET.get('route_id')
    if not route_id:
        return JsonResponse({'error': 'No route ID provided'}, status=400)
    try:
        assigned_clients = Clients.objects.filter(route_id=route_id).values('Client_Code', 'Client_Description')
        available_clients = Clients.objects.filter(route_id__isnull=True).values('Client_Code', 'Client_Description')
        return JsonResponse({'assigned_clients': list(assigned_clients), 'available_clients': list(available_clients)})
    except Exception as e:
        logger.error(f"Error fetching route clients for route_id {route_id}: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def assign_client_to_route(request):
    if request.method == 'POST':
        client_id = request.POST.get('client_id')
        route_id = request.POST.get('route_id')
        action = request.POST.get('action', 'assign')

        if not client_id or not route_id:
            return JsonResponse({'success': False, 'error': 'Client ID and Route ID are required'}, status=400)

        try:
            client = Clients.objects.get(pk=client_id)
            if action == 'assign':
                client.route_id = route_id
            elif action == 'remove':
                client.route_id = None
            client.save()
            return JsonResponse({'success': True})
        except Clients.DoesNotExist:
            logger.error(f"Client with id {client_id} does not exist.")
            return JsonResponse({'success': False, 'error': 'Client does not exist'}, status=400)
        except Exception as e:
            logger.error(f"Error assigning/removing client {client_id} to/from route {route_id}: {str(e)}")
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)
@login_required
def affectation_routes_users(request):
    if request.method == 'GET' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        action = request.GET.get('action')
        if action == 'get_users':
            users = InternalUser.objects.all().values('UserCode', 'UserName')
            return JsonResponse(list(users), safe=False)
        elif action == 'get_user_routes':
            user_code = request.GET.get('user_code')
            if not user_code:
                return JsonResponse({'error': 'No user code provided'}, status=400)

            with connection.cursor() as cursor:
                cursor.execute("SELECT Route_ID, Route_Description FROM Routes WHERE UserCode IS NULL")
                unlinked_routes = cursor.fetchall()

                cursor.execute("SELECT Route_ID, Route_Description FROM Routes WHERE UserCode = %s", [user_code])
                linked_routes = cursor.fetchall()

            unlinked_routes = [{'Route_ID': row[0], 'Route_Description': row[1]} for row in unlinked_routes]
            linked_routes = [{'Route_ID': row[0], 'Route_Description': row[1]} for row in linked_routes]
            return JsonResponse({'unlinked_routes': unlinked_routes, 'linked_routes': linked_routes})

    users = InternalUser.objects.all().values('UserCode', 'UserName')
    return render(request, 'routes/affectation_routes_users.html', {'users': users})

@csrf_exempt
def assign_user_to_route(request):
    if request.method == 'POST':
        route_id = request.POST.get('route_id')
        user_code = request.POST.get('user_code')
        action = request.POST.get('action')

        if not route_id or not user_code:
            return JsonResponse({'success': False, 'error': 'Invalid data'})

        with connection.cursor() as cursor:
            if action == 'remove':
                cursor.execute("UPDATE Routes SET UserCode = NULL WHERE Route_ID = %s", [route_id])
            else:
                cursor.execute("UPDATE Routes SET UserCode = %s WHERE Route_ID = %s", [user_code, route_id])

        return JsonResponse({'success': True})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})




@login_required
def define_device(request):
    if request.method == 'POST':
        # Fetching data from form fields
        device_serial = request.POST.get('device_serial')
        device_type = request.POST.get('device_type')
        device_brand = request.POST.get('device_brand')
        device_status = request.POST.get('device_status')

        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO Devices (DeviceSerial, DeviceStatus, DeviceBrand, DeviceType)
                VALUES (%s, %s, %s, %s)
            """, [device_serial, device_status, device_brand, device_type])

        messages.success(request, 'Device added successfully.')
        return redirect('devices')

    # Render devices page with context if needed
    devices = get_all_devices()  # Assuming a function to fetch all devices
    return render(request, 'devices/home.html', {'devices': devices})
def devices(request):
    username = request.GET.get('username', '')
    device_status = request.GET.get('device_status', '')
    device_type = request.GET.get('device_type', '')
    device_brand = request.GET.get('device_brand', '')
    device_serial = request.GET.get('device_serial', '')

    query = """
        SELECT 
            u.UserCode,
            u.UserName,
            d.DeviceType,
            d.DeviceBrand,
            d.DeviceSerial,
            d.DeviceStatus
        FROM 
            Devices d
        LEFT JOIN 
            User_Device_Registration udr ON d.DeviceSerial = udr.DeviceSerialID
        LEFT JOIN 
            users u ON u.UserCode = udr.UserCode
        WHERE 
            (u.Grouping = 1 OR u.Grouping IS NULL)
            AND (u.UserName LIKE %s OR %s = '')
            AND (d.DeviceStatus = %s OR %s = '')
            AND (d.DeviceType = %s OR %s = '')
            AND (d.DeviceBrand = %s OR %s = '')
            AND (d.DeviceSerial LIKE %s OR %s = '')
    """

    try:
        with connection.cursor() as cursor:
            cursor.execute(query, [
                f'%{username}%', username,
                device_status, device_status,
                device_type, device_type,
                device_brand, device_brand,
                f'%{device_serial}%', device_serial
            ])
            devices_data = cursor.fetchall()
    except Exception as e:
        logger.error(f"Error executing query: {str(e)}")
        return JsonResponse({'status': 'failed', 'message': 'Error fetching devices'}, status=500)

    devices_list = [{
        'UserCode': row[0] or 'Unassigned',
        'UserName': row[1] or 'Unassigned',
        'DeviceType': row[2],
        'DeviceBrand': row[3],
        'DeviceSerial': row[4],
        'DeviceStatus': row[5],
    } for row in devices_data]

    return render(request, 'devices/home.html', {'devices': devices_list})




@csrf_exempt
def update_device(request):
    if request.method == 'POST':
        try:
            user_code = request.POST.get('userCode')
            device_serial = request.POST.get('deviceSerial')
            device_type = request.POST.get('deviceType')
            device_brand = request.POST.get('deviceBrand')
            device_status = request.POST.get('deviceStatus')
            registration_date = timezone.now()


            logger.debug(
                f"Received data: UserCode={user_code}, DeviceSerial={device_serial}, DeviceType={device_type}, DeviceBrand={device_brand}, DeviceStatus={device_status}")

            if not (user_code and device_serial and device_type and device_brand and device_status):
                logger.error("Missing required POST data")
                return JsonResponse({'status': 'failed', 'message': 'Missing required data.'}, status=400)

            update_device_query = """
                UPDATE Devices 
                SET 
                    DeviceType = %s,
                    DeviceBrand = %s,
                    DeviceStatus = %s
                WHERE 
                    DeviceSerial = %s;
            """

            insert_user_device_query = """
                INSERT INTO User_Device_Registration (UserCode, DeviceSerialID, RegistrationDate)
                VALUES (%s, %s, %s)
                ON CONFLICT (DeviceSerialID) 
                DO UPDATE SET UserCode = EXCLUDED.UserCode;
            """

            with transaction.atomic():
                with connection.cursor() as cursor:
                    cursor.execute(update_device_query, [device_type, device_brand, device_status, device_serial])
                    cursor.execute(insert_user_device_query, [user_code, device_serial, registration_date])

            logger.info("Device updated successfully")
            return JsonResponse({'status': 'success'})

        except Exception as e:
            logger.error(f"Error updating device: {str(e)}", exc_info=True)
            return JsonResponse({'status': 'failed', 'message': str(e)}, status=500)

    else:
        return JsonResponse({'status': 'failed', 'message': 'Invalid request method'}, status=400)

# Load devices for display
def load_devices(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    DeviceSerial, 
                    DeviceStatus, 
                    DeviceBrand, 
                    DeviceType 
                FROM Devices
            """)
            devices_data = cursor.fetchall()
    except Exception as e:
        logger.error(f"Error loading devices: {str(e)}")
        return JsonResponse({'status': 'failed', 'message': 'Error loading devices'}, status=500)

    devices_list = [{
        'DeviceSerial': row[0],
        'DeviceStatus': row[1],
        'DeviceBrand': row[2],
        'DeviceType': row[3]
    } for row in devices_data]

    return JsonResponse({'devices': devices_list})

# Fetch users
def fetch_users(request):
    query = """
        SELECT UserCode, UserName FROM users WHERE Grouping = 1
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute(query)
            users_data = cursor.fetchall()
    except Exception as e:
        logger.error(f"Error fetching users: {str(e)}")
        return JsonResponse({'status': 'failed', 'message': 'Error fetching users'}, status=500)

    users_list = [{'UserCode': row[0], 'UserName': row[1]} for row in users_data]

    return JsonResponse({'users': users_list})
def fetch_devices(request):
    query = """
        SELECT * FROM devices 
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute(query)
            devices_data = cursor.fetchall()
    except Exception as e:
        logger.error(f"Error fetching devices: {str(e)}")
        return JsonResponse({'status': 'failed', 'message': 'Error fetching devices'}, status=500)

    devices_list = [{'DeviceSerial': row[0],'DeviceStatus': row[1], 'DeviceBrand': row[2], 'DeviceType': row[3]} for row in devices_data]

    return JsonResponse({'devices': devices_list})



def clients(request):
    query = """
        SELECT 
            Client_Code,
            Client_Description,
            Channel_Code AS Channel,
            Phone_Number,
            Address
        FROM Clients 
    """
#            (SELECT UserName FROM users WHERE User_Code = c.User_Code) AS Salesman,

    with connection.cursor() as cursor:
        cursor.execute(query)
        clients_data = cursor.fetchall()

    clients_list = []
    for row in clients_data:
        client = {
            'Client_Code': row[0],  # Correspond à Client_Code
            'Client_Description': row[1],  # Correspond à Client_Description
            'Channel': row[2],  # Correspond à Channel_Code (Channel)
            'PhoneNumber': row[3],  # Correspond à Phone_Number
            'Address': row[4],  # Correspond à Address
        }
        clients_list.append(client)

    return render(request, 'clients/home.html', {'clients': clients_list})
