*** Settings ***
Library             RequestsLibrary
Resource            common.resource

Suite Setup         Create Session    petstore    ${BASE_URL}


*** Test Cases ***
Get Inventory
    [Tags]    smoke
    GET On Session    petstore    /store/inventory

Place Order
    [Tags]    smoke
    POST On Session    petstore    /store/order    json=${{ {"id": 7, "petId": 1, "quantity": 2, "status": "placed"} }}

Get Order
    [Tags]    regression
    GET On Session    petstore    /store/order/7

Missing Order Returns 404
    [Tags]    regression
    GET On Session    petstore    /store/order/99999    expected_status=404
