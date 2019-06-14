Installation
============

This software is compatible with python 2.7 (the default for CentOS7),
and you should also be able to use e.g. python 3.6.

With the correct repositories set up (as on lxplus for example), you
can get a shell defaulting to python 3.6 with:

```
> scl enable rh-python36 bash
```

The main additional dependency is the requests python module. If
pip is available (by default on more recent pythons), this can be
installed using:

```
> pip install --user requests
```

Alternatively, you might install it as a system package
(eg CentOS 7):

```
> sudo yum install python-requests
```

For some of the test uploading, the requests-toolbelt
package is also used:

```
> pip install --user requests-toolbelt
> sudo yum install python-requests-toolbelt
```

Authentication
==============

In order to use, you need a login for the production DB.

If you have a token, you can store it in the environment
variable ITK_DB_AUTH:

```
> export ITK_DB_AUTH=TOKEN
```

Otherwise, a password is requested.

The two can be combined:

```
> python get_token.py
```

Reading examples
================

To run, use something like:

```
> python read_db.py list_components # Defaults to Strips project
> python read_db.py list_commands
```

All of the .py files in this repository (except for dbAccess.py) are
designed to be run in this manner and help information can be found
by for example:

```
> python add_comment.py --help
```

More example commands:

```
> python read_db.py list_test_types --project S --component-type HYBRID
> python read_db.py list_component_types # Default to Strips
> python read_db.py list_component_types --project P
```

### Component info

You can read all component info using the following:

```
> python read_db.py get_component_info --component-id COMPONENT_CODE
```

where COMPONENT_CODE is either the code (see the QR code), or the serial number.

Writing
=======

A few commands are available to write to the database.

In general these require a code parameter to identify a particular
component. This can be found in the output of the following:

```
> python read_db.py list_components
```

Or, more specifically:

```
> python read_db.py list_components --component-type HYBRID
```

### Test uploads

#### Preparation

In order to upload some test results, you need to generate a json
object, and put it in a file. You can make a prototype of what is
expected for a particular component test with the following:

```
> python test_prototype.py --project S --component-type HYBRID
```

This will create a prototype_XXX.json file for every test type
of that component.

In order to generate a prototype for only one test, use:

```
> python test_prototype.py --project S --component-type HYBRID --test-type STROBE_DELAY
```

(which writes only prototype_STROBE_DELAY.json)


#### The upload

Upload the data with (as before $CODE is the component code):

```
> python upload_test_results.py --test-file file.json --code $CODE
```

### Attachments

You can add an attachment to a component with:

```
> python add_attachment.py --code $CODE --file file-to-read -title "Some short description" --message "Some longer description"
```

The DB can be given a different file name using the argument
--file-name-override.

### Comments

Add a comment to a specific component (different to a comment on a test run).

```
> python add_comment.py --help
```

### Testing

Create a random hybrid and some chips and assemble one on the other:

```
> python make_test.py hybrid
```

TODO
====

Expand to exercise more APIs.

Currently, this mainly reads from the database.

Standard install
================

A more standard python installation method can be used, this is currently a
work-in-progress.

```
pip install --user -e .
```

This installs in user local directory ~/.local/bin, the -e option means 
changes you make in this directory will be used.
