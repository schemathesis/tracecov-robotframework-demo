*** Settings ***
Library             RequestsLibrary
Resource            common.resource

Suite Setup         Create Session    petstore    ${BASE_URL}


*** Test Cases ***
Create User
    [Tags]    smoke
    POST On Session    petstore    /user    json=${{ {"username": "user1", "email": "user1@example.com", "userStatus": 1} }}

Log In
    [Tags]    smoke
    GET On Session    petstore    /user/login    params=username=user1&password=secret

Get User
    [Tags]    regression
    GET On Session    petstore    /user/user1

Missing User Returns 404
    [Tags]    regression
    GET On Session    petstore    /user/nobody    expected_status=404

Log Out
    [Tags]    regression
    GET On Session    petstore    /user/logout
