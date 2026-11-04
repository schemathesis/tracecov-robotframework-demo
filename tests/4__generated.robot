*** Settings ***
Library             SchemathesisLibrary    path=${CURDIR}/../openapi.json    base_url=http://localhost:8080/api/v3    max_examples=5

Test Template       Wrapper
Test Tags           generated


*** Test Cases ***
All Tests    # DataDriver replaces this with one test per generated case
    Wrapper    test_case_1


*** Keywords ***
Wrapper
    [Arguments]    ${case}
    Call And Validate    ${case}
