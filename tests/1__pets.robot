*** Settings ***
Library             RequestsLibrary
Resource            common.resource

Suite Setup         Create Session    petstore    ${BASE_URL}


*** Test Cases ***
Find Available Pets
    [Tags]    smoke
    GET On Session    petstore    /pet/findByStatus    params=status=available

Find Pets By Tags
    [Tags]    regression
    GET On Session    petstore    /pet/findByTags    params=tags=tag1

Get Pet By Id
    [Tags]    smoke
    GET On Session    petstore    /pet/1

Missing Pet Returns 404
    [Tags]    regression
    GET On Session    petstore    /pet/99999    expected_status=404

Reject Unknown Status
    [Tags]    regression
    GET On Session    petstore    /pet/findByStatus    params=status=bogus    expected_status=400

Create Pet
    [Tags]    smoke
    POST On Session    petstore    /pet    json=${{ {"id": 100, "name": "Tom", "photoUrls": [], "status": "available"} }}

Update Pet
    [Tags]    regression
    PUT On Session    petstore    /pet    json=${{ {"id": 100, "name": "Tom", "photoUrls": [], "status": "sold"} }}

Create Pet Without Id
    [Documentation]    Fails: Petstore returns 500 when the body has no `id`.
    [Tags]    regression
    POST On Session    petstore    /pet    json=${{ {"name": "Jerry", "photoUrls": []} }}

Delete Missing Pet
    [Documentation]    Fails: Petstore returns 200, but the spec documents only 400.
    [Tags]    regression
    DELETE On Session    petstore    /pet/99999    expected_status=400
