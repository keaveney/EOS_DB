
def test_list_mock(mocker, capsys):
    m = mocker.patch('itk_pdb.dbAccess.doSomething')
    m.return_value = {"pageItemList": [
        {'code': 'COMPA', 'name': u'Hybrid Type A'},
        {u'code': u'COMPB', 'name': 'Module Type B'}
    ]}

    import read_db
    read_db.list_component_type_codes(project = "S")

    captured = capsys.readouterr()
    output = captured[0]

    assert 'COMPA: Hybrid Type A' in output
    assert 'COMPB: Module Type B' in output

get_component_input = {
        "serialNumber": "50USE000000555",
        "state": "ready",
        "project": { "code": "S", "name": "Strips" },
        "subproject": { "code": "SP", "name": "Sub project" },
        "institution": { "code": "INST", "name": "Testing University" },
        "currentLocation": {
            "code": "INSTB",
            "name": "Another Testing University"
        },
        "user": {
            "userIdentity": "555-555",
            "firstName": "Test",
            "lastName": "Person"
        },
        "componentType": { "code": "HYBRID", "name": "Hybrid" },
        "type": { "code": "R0H0", "name": "R0_H0" },
        "properties": [
            { "code": "RFID", "name": "RFID tag value", "value": "000555" },
            { "code": "NAME", "name": "Name", "value": "SomeName" }
        ],
        'comments':
            [{'code': 'f71b32de3580dddf05cc23e6',
              'dateTime': '2011-01-02T12:34:45+00:00',
              'comment': 'test',
              'user': {'userIdentity': '1234567',
                       'lastName': 'Test', 'firstName': 'Person'}}], 
        'attachments':
            [{'code': '060e41e24e2b2c516bab478bc8c30793a4a4eccbe4db909fbcb5813b4c4c754a',
              'dateTime': '2019-03-05T18:37:35+01:00',
              'type': 'file', 'filename': 'file/test.data',
              'url': None,
              'title': 'this is a test attachment',
              'description': 'delete this attachment if you see it',
              'user': {'userIdentity': '12345-1', 'lastName': 'Other', 'firstName': 'Some'},
              'contentType': 'text/plain'}],
        "children": [
            {
                "componentType": { "code": "HCC", "name": "HCC CMOS Chip" },
                "type": { "code": "HCC130", "name": "HCC130" },
                "id": "012345678"
            },
            {
                "componentType": { "code": "ABC", "name": "ABC CMOS Chip" },
                "type": { "code": "ABC130", "name": "ABC130" },
                "id": "012345"
            },
            {
                "componentType": { "code": "ABC", "name": "ABC CMOS Chip",
                                   "id": "012345" },
                "type": { "code": "ABC130", "name": "ABC130" },
                "id": "543210"
            }
        ],
        "stages": [
            { "code": "BARE", "name": "Bare" }
        ],
    }

def test_get_component_info(mocker, capsys):
    m = mocker.patch('itk_pdb.dbAccess.doSomething')
    m.return_value = get_component_input
    # import sys
    # assert sys.path is None

    import read_db
    # read_db.dbAccess.verbose = True
    read_db.commands["get_component_info"].run(project = "S")

    captured = capsys.readouterr()
    output = captured[0]

    assert captured[1] == ""

    assert "componentType: Hybrid (HYBRID)" in output
    assert "currentLocation: Another Testing University (INSTB)" in output

    assert "children (3)" in output

    assert "unknown dict" not in output
    assert "b'" not in output

list_component_types_input = {"pageItemList": [
    {'name': 'Some CMOS Chip',
     'testTypes': [],
     'properties': [{'name': 'Chip ID',
                     'snPosition': None,
                     'description': '',
                     'default': True,
                     'codeTable': [{'code': '',
                                    'value': ''}],
                     'dataType': 'string',
                     'code': 'ID',
                     'required': True}],
     'types': [{'name': 'Type1',
                'code': 'TYPE1CODE'},
               {'name': 'Type2',
                'code': 'TYPE2CODE'}],
     'code': 'CMOS'},
    {'name': 'Some Wafer',
     'subprojects': [{'name': 'Strip general',
                      'code': 'SG'}],
     'testTypes': ['5a33983726bc9f0005e291bd',
                   '5a3398dc26bc9f0005e291bf'],
     'properties': [{'name': 'Height',
                     'code': 'HEIGHT'},
                    {'name': 'Wafername',
                     'description': 'Name of wafer',
                     'dataType': 'string',
                     'code': 'WAFERNAME'}],
     'types': [{'name': 'Type1',
                'code': 'TYPE1',
                'version': 'prototype'},
               {'name': 'Type2',
                'code': 'TYPE2'}],
     'code': 'WAFER',
     'stages': [{'name': 'Wafer Reception',
                 'initial': True,
                 'order': 1,
                 'code': 'RECEPTION',
                 'final': False},
                {'name': 'Electrical',
                 'initial': False,
                 'order': 2,
                 'code': 'ELECTRICAL',
                 'final': False},
                {'name': 'Decision',
                 'initial': False,
                 'order': 3,
                 'code': 'DECISION',
                 'final': True}]}]}

def test_list_component_types(mocker, capsys):
    m = mocker.patch('itk_pdb.dbAccess.doSomething')
    m.return_value = list_component_types_input

    import read_db
    # read_db.dbAccess.verbose = True
    read_db.commands["list_component_types"].run(project = "S")

    captured = capsys.readouterr()
    output = captured[0]

    assert captured[1] == ""

    assert "Some Wafer (WAFER)" in output
    assert "Wafername (WAFERNAME)" in output

    assert "unknown dict" not in output
    assert "Unexpected type" not in output
    assert "b'" not in output
