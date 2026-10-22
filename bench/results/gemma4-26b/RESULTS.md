# Bug Diary benchmark: gemma4:26b

Memory frozen at 2021-01-01.

## Cards

| variant | cards | symptom stated | symptom inferred | symptom unknown | quotes rejected | median time |
|---|---|---|---|---|---|---|
| code | 66 | 0 | 29 | 37 | 5 | 10 s |
| code+tests | 66 | 3 | 57 | 6 | 1 | 13 s |
| code+tests+message | 66 | 9 | 56 | 1 | 1 | 16 s |
| full | 66 | 62 | 2 | 2 | 0 | 16 s |

## Detection

| diary built from | items checked | relevant lesson retrieved | alert with a lesson of the same family | alert on the fixed lines | same repo | other repo | alerts on fixed code | alerts on healthy changes | median time |
|---|---|---|---|---|---|---|---|---|---|
| code, each lesson alone | 184 (0 failed) | 89/92 | 36/92 | 26/92 | 1/92 | 36/92 | 20/92 | – | 35 s |
| code+tests, each lesson alone | 184 (0 failed) | 90/92 | 29/92 | 17/92 | 0/92 | 29/92 | 11/92 | – | 33 s |
| code+tests+message, each lesson alone | 184 (0 failed) | 90/92 | 29/92 | 21/92 | 2/92 | 29/92 | 11/92 | – | 36 s |
| full, each lesson alone | 205 (0 failed) | 90/92 | 33/92 | 21/92 | 3/92 | 31/92 | 14/92 | 1/21 | 38 s |
| full, by kind of bug (--by-kind) | 205 (0 failed) | 89/92 | 21/92 | 14/92 | 1/92 | 20/92 | 6/92 | 1/21 | 22 s |
| full, experiment: by kind, told guards can be incomplete | 205 (0 failed) | 90/92 | 53/92 | 39/92 | 8/92 | 46/92 | 50/92 | 3/21 | 22 s |
| no diary | 205 (0 failed) | – | – | 52/92 | – | – | 90/92 | 18/21 | 7 s |

## Vulnerable and fixed versions of the same bug

| diary built from | pairs | warns on the vulnerable version only | on both | on neither | on the fixed version only | ordinary commits with a warning |
|---|---|---|---|---|---|---|
| code, each lesson alone | 92 | 19 | 17 | 53 | 3 | – |
| code+tests, each lesson alone | 92 | 22 | 7 | 59 | 4 | – |
| code+tests+message, each lesson alone | 92 | 21 | 8 | 60 | 3 | – |
| full, each lesson alone | 92 | 24 | 9 | 54 | 5 | 1/21 |
| full, by kind of bug (--by-kind) | 92 | 18 | 3 | 68 | 3 | 1/21 |
| full, experiment: by kind, told guards can be incomplete | 92 | 13 | 40 | 29 | 10 | 3/21 |
| no diary, any problem | 92 | 1 | 89 | 1 | 1 | 18/21 |
| no diary, on the lines the fix changed | 92 | 8 | 44 | 22 | 18 | 18/21 |

## By family (full context, each lesson alone)

| family | vulnerable snapshots | relevant lesson retrieved | alert, same family | alert on the fixed lines | no diary: flagged the fixed lines | alerts on fixed code |
|---|---|---|---|---|---|---|
| F1 credentials kept across a redirect | 39 | 38/39 | 11/39 | 6/39 | 15/39 | 0/39 |
| F2 archive extraction escapes its folder | 25 | 24/25 | 9/25 | 5/25 | 18/25 | 8/25 |
| F3 prototype pollution | 20 | 20/20 | 9/20 | 8/20 | 16/20 | 1/20 |
| F4 request smuggling | 8 | 8/8 | 4/8 | 2/8 | 3/8 | 5/8 |

## Alerts on fixed code (each lesson alone)

| fixed snapshot | lesson cited | same family | a later advisory in the same repository |
|---|---|---|---|
| F4-09:fixed | BUG-0048 improperly parsing comma separated header values | yes | F4-10 |
| F2-25:fixed | BUG-0021 improper limitation of pathname to restricted directory | yes | F2-27, F2-28, F2-40, F2-41, F2-42, F2-44, F2-45, F2-46 |
| F2-27:fixed | BUG-0054 path traversal via unsanitized archive entries | yes | F2-28, F2-40, F2-41, F2-42, F2-44, F2-45, F2-46 |
| F2-27:fixed | BUG-0022 directory traversal via relative path manipulation | yes | F2-28, F2-40, F2-41, F2-42, F2-44, F2-45, F2-46 |
| F4-11:fixed | BUG-0041 allowing whitespace before delimiters in protocol headers | yes | F4-14 |
| F4-13:fixed | BUG-0045 allowing conflicting HTTP headers | yes | none |
| F2-30:fixed | BUG-0024 improper limitation of pathname to restricted directory | yes | none |
| F2-30:fixed | BUG-0018 improper validation of file paths | yes | none |
| F3-39:fixed | BUG-0064 Allowing modification of sensitive object properties | yes | none |
| F4-15:fixed | BUG-0057 improper validation of delimited string values | yes | none |
| F4-16:fixed | BUG-0045 allowing conflicting HTTP headers | yes | none |
| F2-35:fixed | BUG-0023 arbitrary file overwrite via symlinks or hardlinks | yes | F2-36, F2-38 |
| F2-36:fixed | BUG-0018 improper validation of file paths | yes | F2-38 |
| F2-37:fixed | BUG-0018 improper validation of file paths | yes | none |
| F2-38:fixed | BUG-0018 improper validation of file paths | yes | none |
| F2-41:fixed | BUG-0012 path traversal via unvalidated archive entries | yes | F2-42, F2-44, F2-45, F2-46 |

## By family (full context, by kind of bug (--by-kind))

| family | vulnerable snapshots | relevant lesson retrieved | alert, same family | alert on the fixed lines | no diary: flagged the fixed lines | alerts on fixed code |
|---|---|---|---|---|---|---|
| F1 credentials kept across a redirect | 39 | 38/39 | 8/39 | 4/39 | 15/39 | 0/39 |
| F2 archive extraction escapes its folder | 25 | 24/25 | 6/25 | 6/25 | 18/25 | 3/25 |
| F3 prototype pollution | 20 | 19/20 | 5/20 | 4/20 | 16/20 | 1/20 |
| F4 request smuggling | 8 | 8/8 | 2/8 | 0/8 | 3/8 | 2/8 |

## Alerts on fixed code (by kind of bug (--by-kind))

| fixed snapshot | lesson cited | same family | a later advisory in the same repository |
|---|---|---|---|
| F4-09:fixed | BUG-0048 improperly parsing comma separated header values | yes | F4-10 |
| F2-25:fixed | BUG-0021 improper limitation of pathname to restricted directory | yes | F2-27, F2-28, F2-40, F2-41, F2-42, F2-44, F2-45, F2-46 |
| F4-11:fixed | BUG-0041 allowing whitespace before delimiters in protocol headers | yes | F4-14 |
| F3-39:fixed | BUG-0064 Allowing modification of sensitive object properties | yes | none |
| F3-39:fixed | BUG-0066 allowing unsafe property names in object parsing | yes | none |
| F2-37:fixed | BUG-0018 improper validation of file paths | yes | none |
| F2-41:fixed | BUG-0012 path traversal via unvalidated archive entries | yes | F2-42, F2-44, F2-45, F2-46 |

## By family (full context, experiment: by kind, told guards can be incomplete)

| family | vulnerable snapshots | relevant lesson retrieved | alert, same family | alert on the fixed lines | no diary: flagged the fixed lines | alerts on fixed code |
|---|---|---|---|---|---|---|
| F1 credentials kept across a redirect | 39 | 38/39 | 24/39 | 17/39 | 15/39 | 18/39 |
| F2 archive extraction escapes its folder | 25 | 24/25 | 13/25 | 11/25 | 18/25 | 17/25 |
| F3 prototype pollution | 20 | 20/20 | 11/20 | 10/20 | 16/20 | 9/20 |
| F4 request smuggling | 8 | 8/8 | 5/8 | 1/8 | 3/8 | 6/8 |

## Alerts on fixed code (experiment: by kind, told guards can be incomplete)

| fixed snapshot | lesson cited | same family | a later advisory in the same repository |
|---|---|---|---|
| F4-09:fixed | BUG-0048 improperly parsing comma separated header values | yes | F4-10 |
| F4-10:fixed | BUG-0045 allowing conflicting HTTP headers | yes | none |
| F2-23:fixed | BUG-0006 directory traversal via path manipulation | yes | F2-24, F2-25, F2-27, F2-28, F2-40, F2-41, F2-42, F2-44, F2-45, F2-46 |
| F2-24:fixed | BUG-0019 unsafe reuse of existing filesystem entries | yes | F2-25, F2-27, F2-28, F2-40, F2-41, F2-42, F2-44, F2-45, F2-46 |
| F2-25:fixed | BUG-0021 improper limitation of pathname to restricted directory | yes | F2-27, F2-28, F2-40, F2-41, F2-42, F2-44, F2-45, F2-46 |
| F2-25:fixed | BUG-0012 path traversal via unvalidated archive entries | yes | F2-27, F2-28, F2-40, F2-41, F2-42, F2-44, F2-45, F2-46 |
| F2-27:fixed | BUG-0012 path traversal via unvalidated archive entries | yes | F2-28, F2-40, F2-41, F2-42, F2-44, F2-45, F2-46 |
| F2-28:fixed | BUG-0004 unvalidated path resolution in file extraction | yes | F2-40, F2-41, F2-42, F2-44, F2-45, F2-46 |
| F3-28:fixed | BUG-0036 Prototype pollution via constructor property | yes | F3-31 |
| F3-31:fixed | BUG-0064 Allowing modification of sensitive object properties | yes | none |
| F4-11:fixed | BUG-0041 allowing whitespace before delimiters in protocol headers | yes | F4-14 |
| F4-12:fixed | BUG-0044 missing delimiter in parser | yes | none |
| F3-33:fixed | BUG-0052 untrusted input modifies object prototypes | yes | none |
| F1-10:fixed | BUG-0027 leaking credentials on protocol downgrade | yes | none |
| F3-34:fixed | BUG-0009 prototype pollution via special keys | yes | none |
| F1-12:fixed | BUG-0001 leaking sensitive headers during cross-origin redirects | yes | none |
| F1-13:fixed | BUG-0056 leaking sensitive credentials during cross-domain redirects | yes | F1-25, F1-29 |
| F4-13:fixed | BUG-0057 improper validation of delimited string values | yes | none |
| F3-35:fixed | BUG-0025 uncontrolled prototype property modification | yes | none |
| F2-30:fixed | BUG-0018 improper validation of file paths | yes | none |
| F1-15:fixed | BUG-0008 leaking sensitive headers during redirects | yes | F1-33, F1-35, F1-37, F1-47 |
| F3-37:fixed | BUG-0036 Prototype pollution via constructor property | yes | F3-40 |
| F3-39:fixed | BUG-0064 Allowing modification of sensitive object properties | yes | none |
| F3-39:fixed | BUG-0042 asymmetric circular reference equality check | yes | none |
| F3-39:fixed | BUG-0066 allowing unsafe property names in object parsing | yes | none |
| F1-20:fixed | BUG-0027 leaking credentials on protocol downgrade | yes | none |
| F2-31:fixed | BUG-0016 improper limitation of pathname to restricted directory | yes | F2-37 |
| F3-40:fixed | BUG-0036 Prototype pollution via constructor property | yes | none |
| F2-33:fixed | BUG-0012 path traversal via unvalidated archive entries | yes | none |
| F4-16:fixed | BUG-0045 allowing conflicting HTTP headers | yes | none |
| F1-25:fixed | BUG-0027 leaking credentials on protocol downgrade | yes | F1-29 |
| F1-26:fixed | BUG-0027 leaking credentials on protocol downgrade | yes | F1-32 |
| F1-28:fixed | BUG-0027 leaking credentials on protocol downgrade | yes | none |
| F1-31:fixed | BUG-0056 leaking sensitive credentials during cross-domain redirects | yes | none |
| F2-35:fixed | BUG-0023 arbitrary file overwrite via symlinks or hardlinks | yes | F2-36, F2-38 |
| F1-32:fixed | BUG-0027 leaking credentials on protocol downgrade | yes | none |
| F2-36:fixed | BUG-0004 unvalidated path resolution in file extraction | yes | F2-38 |
| F2-37:fixed | BUG-0018 improper validation of file paths | yes | none |
| F2-38:fixed | BUG-0019 unsafe reuse of existing filesystem entries | yes | none |
| F2-39:fixed | BUG-0004 unvalidated path resolution in file extraction | yes | none |
| F3-42:fixed | BUG-0043 allowing sensitive property access via path strings | yes | none |
| F2-41:fixed | BUG-0012 path traversal via unvalidated archive entries | yes | F2-42, F2-44, F2-45, F2-46 |
| F2-42:fixed | BUG-0004 unvalidated path resolution in file extraction | yes | F2-44, F2-45, F2-46 |
| F2-44:fixed | BUG-0022 directory traversal via relative path manipulation | yes | F2-45, F2-46 |
| F1-34:fixed | BUG-0027 leaking credentials on protocol downgrade | yes | none |
| F2-45:fixed | BUG-0004 unvalidated path resolution in file extraction | yes | F2-46 |
| F1-35:fixed | BUG-0002 leaking sensitive credentials during redirection | yes | F1-37, F1-47 |
| F1-36:fixed | BUG-0056 leaking sensitive credentials during cross-domain redirects | yes | none |
| F1-38:fixed | BUG-0027 leaking credentials on protocol downgrade | yes | none |
| F1-41:fixed | BUG-0001 leaking sensitive headers during cross-origin redirects | yes | none |
| F1-43:fixed | BUG-0027 leaking credentials on protocol downgrade | yes | none |
| F1-45:fixed | BUG-0001 leaking sensitive headers during cross-origin redirects | yes | none |
| F1-46:fixed | BUG-0027 leaking credentials on protocol downgrade | yes | none |
