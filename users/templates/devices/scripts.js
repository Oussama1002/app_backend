<script>$('#defineDeviceModal').on('hidden.bs.modal', function() {
            $(this).find('form')[0].reset();
        });</script>
    <script>
        function editDevice(button) {
            var row = button.parentNode.parentNode;
            var userCode = row.cells[0].innerText;
            var userName = document.getElementById('editUserName').value;

            var deviceSerial = row.cells[2].innerText;
            var deviceType = row.cells[3].innerText;
            var deviceBrand = row.cells[4].innerText;
            var deviceStatus = row.cells[5].innerText;

            document.getElementById('editUserCode').value = userCode;
            document.getElementById('editUserName').value = userName;
            document.getElementById('editDeviceSerial').value = deviceSerial;
            document.getElementById('editDeviceType').value = deviceType;
            document.getElementById('editDeviceBrand').value = deviceBrand;
            document.getElementById('editDeviceStatus').value = deviceStatus;

            $('#editDeviceModal').modal('show');
        }

function saveDevice() {
    var userCode = document.getElementById('editUserCode').value;
    var deviceSerial = document.getElementById('editDeviceSerial').value;
    var deviceType = document.getElementById('editDeviceType').value;
    var deviceBrand = document.getElementById('editDeviceBrand').value;
    var deviceStatus = document.getElementById('editDeviceStatus').value;

    $.ajax({
        url: '{% url "update_device" %}',
        method: 'POST',
        data: {
            csrfmiddlewaretoken: '{{ csrf_token }}',
            deviceSerial: deviceSerial,
            userCode: userCode,
            deviceType: deviceType,
            deviceBrand: deviceBrand,
            deviceStatus: deviceStatus
        },
        success: function(response) {
            alert('Device updated successfully');
        },
        error: function(error) {
            alert('Failed to update device');
        }
    });
}



   function openUsersModal() {
    $.ajax({
        url: '{% url "fetch_users" %}',  // URL for fetching users
        method: 'GET',
        success: function(response) {
            var usersTableBody = document.getElementById('usersTable').querySelector('tbody');
            usersTableBody.innerHTML = ''; // Clear previous rows

            response.users.forEach(function(user) {
                var row = document.createElement('tr');
                row.innerHTML = `
                    <td>${user.UserCode}</td>
                    <td>${user.UserName}</td>
                `;
                row.onclick = function() {
                    selectUser(user.UserCode, user.UserName);
                };
                usersTableBody.appendChild(row);
            });

            $('#usersModal').modal('show'); // Show the modal
        },
        error: function(error) {
            console.error('Failed to fetch users', error);
        }
    });
}
function openDevicesModal() {
    $.ajax({
        url: '{% url "fetch_devices" %}',  // URL for fetching devices
        method: 'GET',
        success: function(response) {
            var devicesTableBody = document.getElementById('devicesTable').querySelector('tbody');
            devicesTableBody.innerHTML = ''; // Clear previous rows

            // Use response.devices instead of response.users
            response.devices.forEach(function(device) {
                var row = document.createElement('tr');
                row.innerHTML = `
                    <td>${device.DeviceSerial}</td>
                    <td>${device.DeviceStatus}</td>
                    <td>${device.DeviceBrand}</td>
                    <td>${device.DeviceType}</td>
                `;
                row.onclick = function() {
                    selectDevice(device.DeviceSerial, device.DeviceStatus, device.DeviceBrand, device.DeviceType);
                };
                devicesTableBody.appendChild(row);
            });

            $('#devicesModal').modal('show'); // Show the modal
        },
        error: function(error) {
            console.error('Failed to fetch devices', error);
        }
    });
}

function selectDevice(deviceSerial, deviceStatus, deviceBrand, deviceType) {
    // Example function to handle device selection
    console.log('Selected device:', deviceSerial, deviceStatus, deviceBrand, deviceType);
    // You can add your logic here to handle the selected device
    $('#devicesModal').modal('hide'); // Close the modal
}




function selectUser(userCode, userName) {
    document.getElementById('editUserCode').value = userCode;
    document.getElementById('editUserName').value = userName;
    $('#usersModal').modal('hide');
}
        document.getElementById('editDeviceSerial').addEventListener('click', openDevicesModal);


        document.getElementById('editUserName').addEventListener('click', openUsersModal);
    </script>
