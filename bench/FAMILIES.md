# Recurring bug families for the Bug Diary benchmark

Cutoff T = 2021-01-01. Generated 2026-10-20. Machine-readable data: `families.json` (same folder); raw API responses in `raw/`, scripts in `scripts/`.

Every fix commit below was fetched with `gh api repos/OWNER/REPO/commits/SHA`; SHAs in `families.json` are the full 40-character values returned by the API. 'verified' means the diff of the primary commit (and listed parts) visibly implements what the advisory describes. Unverified instances are listed but not counted.

Split rule: **memory** = first fix commit and advisory both before T; **eval** = first fix commit on or after T; **straddle** = fix public before T but advisory published after T (the diff existed, the advisory text did not). Advisory date = earliest of GHSA, NVD and vendor dates (many GHSA entries for old CVEs are 2022 re-imports).

## Totals (verified instances)

| Family | Listed | Verified | Memory (< T) | Eval (>= T) | Straddle | Repos | Languages |
|---|---|---|---|---|---|---|---|
| F1 | 48 | 47 | 7 | 39 | 1 | 22 | C, Go, Java, JavaScript, PHP, Python, Ruby |
| F2 | 49 | 48 | 22 | 26 | 0 | 22 | C#, Go, Java, JavaScript, Python, Ruby, Rust |
| F3 | 42 | 42 | 20 | 20 | 2 | 24 | JavaScript |
| F4 | 16 | 16 | 8 | 8 | 0 | 6 | Java, Python, Ruby, Rust |

## F1: HTTP client forwards credentials (Authorization, Cookie, Proxy-Authorization, tokens) when following a redirect to another host, scheme or port

47 verified of 48 listed; 7 memory, 39 eval, 1 straddle; 22 repositories; fit 'core' for 44.

| ID | Repo | Advisory | Fix commit | Fix date | Advisory date | Split | Status | Fit |
|---|---|---|---|---|---|---|---|---|
| F1-01 | psf/requests | CVE-2014-1829 | `7ba5a534ae9f` | 2014-01-29 | 2014-10-15 | memory | verified | core |
| F1-02 | psf/requests | CVE-2014-1830 | `fe4c4f146124` | 2014-03-23 | 2014-10-15 | memory | verified | core |
| F1-03 | rest-client/rest-client | CVE-2015-1820 | `4718d38d6892` | 2015-03-22 | 2017-08-09 | memory | verified | borderline |
| F1-04 | curl/curl | CVE-2018-1000007 | `af32cd385933` | 2018-01-22 | 2018-01-24 | memory | verified | core |
| F1-05 | urllib3/urllib3 | CVE-2018-20060 | `560bd227b90f` | 2018-03-29 | 2018-12-11 | memory | verified | core |
| F1-06 | psf/requests | CVE-2018-18074 | `c45d7c49ea75` | 2018-09-14 | 2018-10-09 | memory | verified | core |
| F1-07 | urllib3/urllib3 | CVE-2018-25091 | `adb358f8e068` | 2018-12-29 | 2023-10-15 | straddle | verified | core |
| F1-08 | actions/http-client | CVE-2020-11021 | `f6aae3dda4f4` | 2020-04-23 | 2020-04-29 | memory | verified | core |
| F1-09 | follow-redirects/follow-redirects | CVE-2022-0155 | `8b347cbcef7c` | 2022-01-10 | 2022-01-10 | eval | verified | core |
| F1-10 | node-fetch/node-fetch | CVE-2022-0235 | `f5d3cf5e2579` | 2022-01-13 | 2022-01-16 | eval | verified | core |
| F1-11 | follow-redirects/follow-redirects | CVE-2022-0536 | `62e546a99c07` | 2022-02-08 | 2022-02-09 | eval | verified | core |
| F1-12 | fluture-js/fluture-node | CVE-2022-24719 | `125e4474f910` | 2022-03-01 | 2022-03-01 | eval | verified | core |
| F1-13 | scrapy/scrapy | CVE-2022-0577 | `8ce01b3b76d4` | 2022-03-01 | 2022-03-01 | eval | verified | core |
| F1-14 | curl/curl | CVE-2022-27776 | `6e659993952a` | 2022-04-25 | 2022-04-27 | eval | verified | core |
| F1-15 | curl/curl | CVE-2022-27774 | `620ea2141003` | 2022-04-25 | 2022-04-27 | eval | verified | core |
| F1-16 | sparklemotion/mechanize | CVE-2022-31033 | `c7fe6996a5b9` | 2022-06-09 | 2022-06-09 | eval | verified | core |
| F1-17 | guzzle/guzzle | CVE-2022-31042, CVE-2022-31043 | `e3ff079b2282` | 2022-06-09 | 2022-06-09 | eval | verified | core |
| F1-18 | guzzle/guzzle | CVE-2022-31090, CVE-2022-31091 | `1dd98b0564cb` | 2022-06-20 | 2022-06-21 | eval | verified | core |
| F1-19 | nodejs/undici | CVE-2022-31151 | `0a5bee9465e6` | 2022-07-18 | 2022-07-21 | eval | verified | core |
| F1-20 | sylabs/scs-library-client | CVE-2022-23538 | `eebd7caaab31` | 2022-12-13 | 2023-01-17 | eval | verified | core |
| F1-21 | psf/requests | CVE-2023-32681 | `74ea7cf7a6a2` | 2023-05-22 | 2023-05-22 | eval | verified | core |
| F1-22 | urllib3/urllib3 | CVE-2023-43804 | `644124ecd0b6` | 2023-10-02 | 2023-10-02 | eval | verified | core |
| F1-23 | nodejs/undici | CVE-2023-45143 | `e041de359221` | 2023-10-11 | 2023-10-12 | eval | verified | core |
| F1-24 | nodejs/undici | CVE-2024-24758 | `b9da3e40f1f0` | 2024-02-05 | 2024-02-16 | eval | verified | core |
| F1-25 | scrapy/scrapy | CVE-2024-3574 | `5bcb8fd5019c` | 2024-02-14 | 2024-02-15 | eval | verified | core |
| F1-26 | golang/go | CVE-2023-45289 | `821bf37819ec` | 2024-03-05 | 2024-03-05 | eval | verified | core |
| F1-27 | follow-redirects/follow-redirects | CVE-2024-28849 | `c4f847f85176` | 2024-03-14 | 2024-03-14 | eval | verified | core |
| F1-28 | nodejs/undici | CVE-2024-30260 | `6805746680d2` | 2024-04-02 | 2024-04-04 | eval | verified | core |
| F1-29 | scrapy/scrapy | CVE-2024-1968 | `1d0502f25bbe` | 2024-05-13 | 2024-05-14 | eval | verified | core |
| F1-30 | urllib3/urllib3 | CVE-2024-37891 | `accff72ecc2f` | 2024-06-17 | 2024-06-17 | eval | verified | core |
| F1-31 | denoland/deno | CVE-2025-21620 | `7456255cd102` | 2024-11-25 | 2025-01-06 | eval | verified | core |
| F1-32 | golang/go | CVE-2024-45336 | `6783377295e0` | 2025-01-16 | 2025-01-28 | eval | verified | core |
| F1-33 | curl/curl | CVE-2025-14524 | `1a822275d333` | 2025-12-11 | 2026-01-07 | eval | verified | core |
| F1-34 | aio-libs/aiohttp | CVE-2026-34518 | `6e8f393330f9` | 2026-02-27 | 2026-04-01 | eval | verified | core |
| F1-35 | curl/curl | CVE-2026-3783 | `e3d7401a32a4` | 2026-03-07 | 2026-03-11 | eval | verified | core |
| F1-36 | follow-redirects/follow-redirects | GHSA-r4q5-vmmm-2653 | `844c4d302ac9` | 2026-04-13 | 2026-04-14 | eval | verified | borderline |
| F1-37 | curl/curl | CVE-2026-6253 | `188c2f166a20` | 2026-04-14 | 2026-04-29 | eval | verified | core |
| F1-38 | go-git/go-git | CVE-2026-41506 | `137874facf92` | 2026-04-16 | 2026-04-17 | eval | verified | core |
| F1-39 | axios/axios | CVE-2026-44486 | `afca61a07072` | 2026-04-22 | 2026-06-04 | eval | verified | core |
| F1-40 | hapijs/wreck | CVE-2026-44979 | `a5b6fac9c684` | 2026-05-06 | 2026-05-27 | eval | verified | core |
| F1-41 | urllib3/urllib3 | CVE-2026-44431 | `5ec0de499b91` | 2026-05-07 | 2026-05-11 | eval | verified | core |
| F1-42 | AsyncHttpClient/async-http-client | CVE-2026-45300 | `3b0e3e9e889f` | 2026-05-12 | 2026-05-18 | eval | verified | core |
| F1-43 | hapijs/wreck | CVE-2026-48022 | `b93323b63ad3` | 2026-05-20 | 2026-06-11 | eval | verified | core |
| F1-44 | tornadoweb/tornado | CVE-2026-49853 | `bc717035f397` | 2026-05-27 | 2026-06-15 | eval | verified | core |
| F1-45 | excon/excon | CVE-2026-54171 | `ea89a35308a1` | 2026-06-03 | 2026-07-10 | eval | verified | core |
| F1-46 | sparklemotion/mechanize | CVE-2026-107715 | `ac49abf28692` | 2026-08-22 | 2026-10-08 | eval | verified | core |
| F1-47 | curl/curl | CVE-2026-86413 | `43029e2ec37e` | 2026-09-09 | 2026-10-14 | eval | verified | borderline |
| F1-48 | reactor/reactor-netty | CVE-2025-22227 | `522892307ea8` | 2025-07-09 | 2025-07-16 | eval | unverified | core |

**Same-repository recurrences** (verified; arrow marks the cutoff):

- curl/curl: F1-04 (2018-01, memory) → T → F1-14 (2022-04, eval) F1-15 (2022-04, eval) F1-33 (2025-12, eval) F1-35 (2026-03, eval) F1-37 (2026-04, eval) F1-47 (2026-09, eval)
- urllib3/urllib3: F1-05 (2018-03, memory) F1-07 (2018-12, straddle) → T → F1-22 (2023-10, eval) F1-30 (2024-06, eval) F1-41 (2026-05, eval)
- follow-redirects/follow-redirects: F1-09 (2022-01, eval) F1-11 (2022-02, eval) F1-27 (2024-03, eval) F1-36 (2026-04, eval)
- nodejs/undici: F1-19 (2022-07, eval) F1-23 (2023-10, eval) F1-24 (2024-02, eval) F1-28 (2024-04, eval)
- psf/requests: F1-01 (2014-01, memory) F1-02 (2014-03, memory) F1-06 (2018-09, memory) → T → F1-21 (2023-05, eval)
- scrapy/scrapy: F1-13 (2022-03, eval) F1-25 (2024-02, eval) F1-29 (2024-05, eval)
- golang/go: F1-26 (2024-03, eval) F1-32 (2025-01, eval)
- guzzle/guzzle: F1-17 (2022-06, eval) F1-18 (2022-06, eval)
- hapijs/wreck: F1-40 (2026-05, eval) F1-43 (2026-05, eval)
- sparklemotion/mechanize: F1-16 (2022-06, eval) F1-46 (2026-08, eval)

**Pairs across the cutoff:**

- Same-repo pairs: 10 of 39 eval instances have at least one memory instance in the same repository: F1-14 (curl/curl), F1-15 (curl/curl), F1-21 (psf/requests), F1-22 (urllib3/urllib3), F1-30 (urllib3/urllib3), F1-33 (curl/curl), F1-35 (curl/curl), F1-37 (curl/curl), F1-41 (urllib3/urllib3), F1-47 (curl/curl).
- Cross-repo pairs: each eval instance has between 4 and 7 memory instances from other repositories (between 3 and 7 in another language family; TypeScript counted with JavaScript).
- Eval instances that can only be matched cross-repo: 29.
- Memory instances: 7; straddle instances: F1-07.

**Notable:**

- psf/requests: the 2014 Proxy-Authorization fix (CVE-2014-1830) added rebuild_proxies(), the code path that leaked Proxy-Authorization to HTTPS origins until CVE-2023-32681 (2023). The 2014 Authorization fix compared hostnames only, which CVE-2018-18074 (https to http on the same host) exploited.
- urllib3/urllib3: the CVE-2018-20060 strip list was case-sensitive and came back as CVE-2018-25091 (fixed Dec 2018, advisory only in 2023). Then Cookie (2023), Proxy-Authorization (2024), and in 2026 the same stripping was found missing in a second code path (HTTPConnectionPool).
- nodejs/undici: four advisories in 2022-2024, each adding one header to one of two redirect code paths (dispatcher Cookie, fetch Cookie, fetch Proxy-Authorization, dispatcher Proxy-Authorization).
- follow-redirects: Cookie (Jan 2022), scheme change (Feb 2022), Proxy-Authorization (2024), custom auth headers (2026, opt-in fix).
- curl/curl: host-only check (2018), then same host with another port or protocol (2022), then bearer tokens in SASL (2025) and HTTP (2026) paths, proxy credentials (2026) and Negotiate connection reuse (2026).
- Same progression in many repositories: strip on host change, then also on scheme or port change (requests, curl, follow-redirects, scrapy, guzzle, mechanize, hapijs/wreck), then add Cookie, then Proxy-Authorization.
- Pre-cutoff memory is thin for this family (7 verified instances: Python, Ruby, C, TypeScript); most instances are 2022 or later.

**Unverified (excluded from counts):** F1-48 reactor/reactor-netty CVE-2025-22227: The only commit referenced by the advisory is about HTTP/2 upgrade stream state and does not touch redirect or credential handling. No public commit implementing the fix was found; excluded from counts.

## F2: Archive extraction writes outside the destination directory (zip slip / tar slip: '..', absolute or drive paths, symlink and hardlink tricks, prefix-only containment checks)

48 verified of 49 listed; 22 memory, 26 eval, 0 straddle; 22 repositories; fit 'core' for 46.

| ID | Repo | Advisory | Fix commit | Fix date | Advisory date | Split | Status | Fit |
|---|---|---|---|---|---|---|---|---|
| F2-01 | isaacs/node-tar | CVE-2015-8860 | `a5337a6cd58a` | 2015-03-27 | 2017-01-23 | memory | verified | core |
| F2-02 | rubyzip/rubyzip | CVE-2017-5946 | `ce4208fdecc2` | 2017-02-08 | 2017-02-27 | memory | verified | core |
| F2-03 | kubernetes/kubernetes | CVE-2018-1002100 | `b9a893813aa7` | 2018-03-18 | 2018-06-02 | memory | verified | core |
| F2-04 | ZJONSSON/node-unzipper | CVE-2018-1002203 | `2220ddd5b58f` | 2018-04-16 | 2018-07-25 | memory | verified | core |
| F2-05 | cthackers/adm-zip | CVE-2018-1002204 | `62f64004fefb` | 2018-04-23 | 2018-07-25 | memory | verified | core |
| F2-06 | zeroturnaround/zt-zip | CVE-2018-1002201 | `759b72f33bc8` | 2018-04-26 | 2018-07-25 | memory | verified | core |
| F2-07 | mafintosh/tar-fs | CVE-2018-20835 | `06672828e6fa` | 2018-04-30 | 2019-04-30 | memory | verified | core |
| F2-08 | isaacs/node-tar | CVE-2018-20834 | `b0c58433c22f` | 2018-04-30 | 2019-04-30 | memory | verified | core |
| F2-09 | adamhathcock/sharpcompress | CVE-2018-1002206 | `80ceb1c375fd` | 2018-05-02 | 2018-07-25 | memory | verified | core |
| F2-10 | codehaus-plexus/plexus-archiver | CVE-2018-1002200 | `f8f423350819` | 2018-05-06 | 2018-07-25 | memory | verified | core |
| F2-11 | haf/DotNetZip.Semverd | CVE-2018-1002205 | `55d2c13c0cc6` | 2018-05-07 | 2018-07-25 | memory | verified | core |
| F2-12 | composefs/tar-rs | CVE-2018-20990 | `54651a87ae6b` | 2018-06-29 | 2019-08-26 | memory | verified | core |
| F2-13 | icsharpcode/SharpZipLib | CVE-2018-1002208 | `5376c2daf1c0` | 2018-07-01 | 2018-07-25 | memory | verified | core |
| F2-14 | rubyzip/rubyzip | CVE-2018-1000544 | `d07b13a6cf0a` | 2018-08-23 | 2018-06-26 | memory | verified | core |
| F2-15 | kubernetes/kubernetes | CVE-2019-1002101 | `47063891dd78` | 2019-03-06 | 2019-04-01 | memory | verified | core |
| F2-16 | kubernetes/kubernetes | CVE-2019-11246 | `b95fca093d29` | 2019-04-30 | 2019-08-29 | memory | verified | core |
| F2-17 | npm/fstream | CVE-2019-13173 | `6a77d2fa6e14` | 2019-05-15 | 2019-05-30 | memory | verified | core |
| F2-18 | kubernetes/kubernetes | CVE-2019-11249 | `08f9f2b58a6a` | 2019-07-22 | 2019-08-29 | memory | verified | core |
| F2-19 | kubernetes/kubernetes | CVE-2019-11251 | `35e0f17a33e4` | 2019-09-03 | 2020-02-03 | memory | verified | core |
| F2-20 | ansible/ansible | CVE-2020-10691 | `a20a52701402` | 2020-03-31 | 2020-04-30 | memory | verified | core |
| F2-21 | kevva/decompress | CVE-2020-12265 | `967146e70f48` | 2020-04-01 | 2020-04-26 | memory | verified | core |
| F2-22 | mholt/archiver | CVE-2019-10743 | `8217ed3a206c` | 2020-09-28 | 2019-10-29 | memory | verified | core |
| F2-23 | isaacs/node-tar | CVE-2021-32804 | `1f036ca23f64` | 2021-07-23 | 2021-08-03 | eval | verified | core |
| F2-24 | isaacs/node-tar | CVE-2021-32803 | `9dbdeb6df8e9` | 2021-07-26 | 2021-08-03 | eval | verified | core |
| F2-25 | isaacs/node-tar | CVE-2021-37701 | `53602669f58d` | 2021-08-04 | 2021-08-31 | eval | verified | core |
| F2-26 | composefs/tar-rs | CVE-2021-38511 | `d90a02f582c0` | 2021-08-10 | 2021-08-10 | eval | verified | core |
| F2-27 | isaacs/node-tar | CVE-2021-37712 | `3aaf19b2501b` | 2021-08-12 | 2021-08-31 | eval | verified | core |
| F2-28 | isaacs/node-tar | CVE-2021-37713 | `875a37e3ec03` | 2021-08-19 | 2021-08-31 | eval | verified | core |
| F2-29 | icsharpcode/SharpZipLib | CVE-2021-32840, CVE-2021-32841 | `5c3b293de5d6` | 2021-09-19 | 2022-01-26 | eval | verified | core |
| F2-30 | Stuk/jszip | CVE-2022-48285 | `2edab366119c` | 2022-03-30 | 2023-01-29 | eval | verified | core |
| F2-31 | python/cpython | CVE-2007-4559 | `af530469954e` | 2023-04-24 | 2007-08-28 | eval | verified | borderline |
| F2-32 | codehaus-plexus/plexus-archiver | CVE-2023-37460 | `54759839fbdf` | 2023-07-25 | 2023-07-25 | eval | verified | core |
| F2-33 | ansible/ansible | CVE-2023-5115 | `ddf0311c6328` | 2023-09-26 | 2023-12-18 | eval | verified | core |
| F2-34 | mhr3/unzip-stream | GHSA-6jrj-vc65-c983 | `ab67989719ab` | 2024-04-20 | 2024-08-26 | eval | verified | core |
| F2-35 | mafintosh/tar-fs | CVE-2024-12905 | `a1dd7e7c7f4b` | 2025-01-12 | 2025-03-27 | eval | verified | core |
| F2-36 | mafintosh/tar-fs | CVE-2025-48387 | `647447b572bc` | 2025-05-22 | 2025-06-02 | eval | verified | core |
| F2-37 | python/cpython | CVE-2025-4517, CVE-2025-4330, CVE-2025-4138, CVE-2024-12718 | `3612d8f51741` | 2025-06-03 | 2025-06-03 | eval | verified | core |
| F2-38 | mafintosh/tar-fs | CVE-2025-59343 | `0bd54cdf06da` | 2025-09-16 | 2025-09-24 | eval | verified | core |
| F2-39 | pypa/pip | CVE-2025-8869 | `f2b92314da01` | 2025-09-24 | 2025-09-24 | eval | verified | core |
| F2-40 | isaacs/node-tar | CVE-2026-23745 | `340eb285b6d9` | 2026-01-16 | 2026-01-16 | eval | verified | core |
| F2-41 | isaacs/node-tar | CVE-2026-23950 | `3b1abfae6500` | 2026-01-19 | 2026-01-20 | eval | verified | borderline |
| F2-42 | isaacs/node-tar | CVE-2026-24842 | `f4a7aa9bc3d7` | 2026-01-27 | 2026-01-28 | eval | verified | core |
| F2-43 | node-modules/compressing | CVE-2026-24884 | `ce1c0131c401` | 2026-01-28 | 2026-02-03 | eval | verified | core |
| F2-44 | isaacs/node-tar | CVE-2026-26960 | `d18e4e1f846f` | 2026-02-13 | 2026-02-18 | eval | verified | core |
| F2-45 | isaacs/node-tar | CVE-2026-29786 | `7bc755dd85e6` | 2026-03-04 | 2026-03-05 | eval | verified | core |
| F2-46 | isaacs/node-tar | CVE-2026-31802 | `f48b5fa3b798` | 2026-03-09 | 2026-03-10 | eval | verified | core |
| F2-47 | node-modules/compressing | CVE-2026-40931 | `9c885e5bd922` | 2026-04-13 | 2026-04-17 | eval | verified | core |
| F2-48 | XhmikosR/decompress | CVE-2026-53486 | `281cefa00cd4` | 2026-05-30 | 2026-07-06 | eval | verified | core |
| F2-49 | actions/toolkit | CVE-2024-42471 | `29885a805ef3` | 2024-04-24 | 2024-09-02 | eval | unverified | core |

**Same-repository recurrences** (verified; arrow marks the cutoff):

- isaacs/node-tar: F2-01 (2015-03, memory) F2-08 (2018-04, memory) → T → F2-23 (2021-07, eval) F2-24 (2021-07, eval) F2-25 (2021-08, eval) F2-27 (2021-08, eval) F2-28 (2021-08, eval) F2-40 (2026-01, eval) F2-41 (2026-01, eval) F2-42 (2026-01, eval) F2-44 (2026-02, eval) F2-45 (2026-03, eval) F2-46 (2026-03, eval)
- kubernetes/kubernetes: F2-03 (2018-03, memory) F2-15 (2019-03, memory) F2-16 (2019-04, memory) F2-18 (2019-07, memory) F2-19 (2019-09, memory)
- mafintosh/tar-fs: F2-07 (2018-04, memory) → T → F2-35 (2025-01, eval) F2-36 (2025-05, eval) F2-38 (2025-09, eval)
- ansible/ansible: F2-20 (2020-03, memory) → T → F2-33 (2023-09, eval)
- codehaus-plexus/plexus-archiver: F2-10 (2018-05, memory) → T → F2-32 (2023-07, eval)
- composefs/tar-rs: F2-12 (2018-06, memory) → T → F2-26 (2021-08, eval)
- icsharpcode/SharpZipLib: F2-13 (2018-07, memory) → T → F2-29 (2021-09, eval)
- node-modules/compressing: F2-43 (2026-01, eval) F2-47 (2026-04, eval)
- python/cpython: F2-31 (2023-04, eval) F2-37 (2025-06, eval)
- rubyzip/rubyzip: F2-02 (2017-02, memory) F2-14 (2018-08, memory)

**Pairs across the cutoff:**

- Same-repo pairs: 18 of 26 eval instances have at least one memory instance in the same repository: F2-23 (isaacs/node-tar), F2-24 (isaacs/node-tar), F2-25 (isaacs/node-tar), F2-26 (composefs/tar-rs), F2-27 (isaacs/node-tar), F2-28 (isaacs/node-tar), F2-29 (icsharpcode/SharpZipLib), F2-32 (codehaus-plexus/plexus-archiver), F2-33 (ansible/ansible), F2-35 (mafintosh/tar-fs), F2-36 (mafintosh/tar-fs), F2-38 (mafintosh/tar-fs), F2-40 (isaacs/node-tar), F2-41 (isaacs/node-tar), F2-42 (isaacs/node-tar), F2-44 (isaacs/node-tar), F2-45 (isaacs/node-tar), F2-46 (isaacs/node-tar).
- Cross-repo pairs: each eval instance has between 20 and 22 memory instances from other repositories (between 15 and 21 in another language family; TypeScript counted with JavaScript).
- Eval instances that can only be matched cross-repo: 8.
- Memory instances: 22; straddle instances: none.

**Notable:**

- isaacs/node-tar has 13 instances (2015-2026). The July 2021 directory-cache fix (CVE-2021-32803) was bypassed a week later with backslashes and case (CVE-2021-37701) and again with Unicode normalisation (CVE-2021-37712). The 2021 drive-relative path fix for entry paths (CVE-2021-37713) came back for link targets in 2026 (CVE-2026-29786 hard links, CVE-2026-31802 symlinks), and the January 2026 linkpath sanitiser (CVE-2026-23745) was bypassed for hard links eleven days later (CVE-2026-24842).
- Prefix-only containment checks (startsWith / indexOf without a trailing separator) were the standard 2018-2020 fix (adm-zip, node-unzipper, zt-zip, plexus-archiver, sharpcompress, mholt/archiver, kevva/decompress) and were later exploited in SharpZipLib (CVE-2021-32840/32841), tar-fs (CVE-2025-59343) and the decompress fork (CVE-2026-53486).
- kubernetes kubectl cp: five CVEs in 18 months (2018-2019); the Kubernetes issue for CVE-2019-11249 calls it an incomplete fix of both CVE-2019-1002101 and CVE-2019-11246, and the last fix (CVE-2019-11251) removed symlink support.
- Other incomplete fixes that came back in the same repository: rubyzip 2017 then 2018, tar-fs 2024 then 2025 (twice), compressing January then April 2026 ('complete bypass'), cpython PEP 706 filters (2023) bypassed in 2025 through realpath behaviour.
- The hard-link overwrite trick appeared in four repositories within a year (node-tar, fstream, tar-fs, tar-rs, 2018-2019).

**Unverified (excluded from counts):** F2-49 actions/toolkit CVE-2024-42471: Excluded from counts. The linked commit only bumps unzip-stream (which received its own fix) and reverts to unzip.Extract. The earlier in-repo check rejects the promise on a bad path but does not stop the write. The advisory text (fixed in 2.1.7) and its version range (fixed in 2.1.2) disagree.

## F3: Prototype pollution: deep merge, path setters, parsers or patch appliers write through __proto__ / constructor.prototype keys (including bypasses through non-string keys)

42 verified of 42 listed; 20 memory, 20 eval, 2 straddle; 24 repositories; fit 'core' for 41.

| ID | Repo | Advisory | Fix commit | Fix date | Advisory date | Split | Status | Fit |
|---|---|---|---|---|---|---|---|---|
| F3-01 | ljharb/qs | CVE-2017-1000048 | `beade029171b` | 2017-02-14 | 2017-07-17 | memory | verified | borderline |
| F3-02 | lodash/lodash | CVE-2018-3721 | `d8e069cc3410` | 2018-01-31 | 2018-06-07 | memory | verified | core |
| F3-03 | hapijs/hoek | CVE-2018-3728 | `32ed5c941332` | 2018-02-06 | 2018-03-30 | memory | verified | core |
| F3-04 | jonschlinkert/merge-deep | CVE-2018-3722 | `2c33634da712` | 2018-02-07 | 2018-06-07 | memory | verified | core |
| F3-05 | unclechu/node-deep-extend | CVE-2018-3750 | `9423fae877e2` | 2018-04-27 | 2018-07-03 | memory | verified | core |
| F3-06 | lodash/lodash | CVE-2018-16487 | `90e6199a161b` | 2018-08-31 | 2019-02-01 | memory | verified | core |
| F3-07 | swordev/merge | CVE-2018-16469 | `6ad6035b901b` | 2018-10-27 | 2018-10-30 | memory | verified | core |
| F3-08 | jquery/jquery | CVE-2019-11358 | `753d591aea69` | 2019-03-25 | 2019-04-20 | memory | verified | core |
| F3-09 | jonschlinkert/mixin-deep | CVE-2019-10746 | `8f464c8ce976` | 2019-06-19 | 2019-08-23 | memory | verified | core |
| F3-10 | jonschlinkert/set-value | CVE-2019-10747 | `95e9d9923f8a` | 2019-06-19 | 2019-08-23 | memory | verified | core |
| F3-11 | lodash/lodash | CVE-2019-10744 | `1f8ea0774696` | 2019-06-24 | 2019-07-10 | memory | verified | core |
| F3-12 | sindresorhus/dot-prop | CVE-2020-8116 | `3039c8c07f6f` | 2019-10-23 | 2020-02-04 | memory | verified | core |
| F3-13 | hapijs/hoek | CVE-2020-36604 | `948baf98634a` | 2020-02-08 | 2022-09-23 | straddle | verified | core |
| F3-14 | dojo/dojo | CVE-2020-5258 | `20a00afb68f5` | 2020-03-10 | 2020-03-10 | memory | verified | core |
| F3-15 | minimistjs/minimist | CVE-2020-7598 | `63e7ed05aa4b` | 2020-03-10 | 2020-03-11 | memory | verified | core |
| F3-16 | yargs/yargs-parser | CVE-2020-7608 | `63810ca1ae1a` | 2020-03-16 | 2020-03-16 | memory | verified | core |
| F3-17 | lodash/lodash | CVE-2020-8203 | `c84fe82760fb` | 2020-07-02 | 2020-07-15 | memory | verified | core |
| F3-18 | hughsk/flat | CVE-2020-36632 | `20ef0ef55dfa` | 2020-08-06 | 2022-12-25 | straddle | verified | core |
| F3-19 | manuelstofer/json-pointer | CVE-2020-7709 | `1dbd1ed6bef7` | 2020-09-24 | 2020-10-05 | memory | verified | core |
| F3-20 | mariocasciaro/object-path | CVE-2020-15256 | `2be3354c6c46` | 2020-10-10 | 2020-10-19 | memory | verified | core |
| F3-21 | yargs/y18n | CVE-2020-7774 | `a9ac604abf75` | 2020-10-25 | 2020-11-17 | memory | verified | core |
| F3-22 | npm/ini | CVE-2020-7788 | `56d2805e07cc` | 2020-12-08 | 2020-12-10 | memory | verified | core |
| F3-23 | jonschlinkert/merge-deep | CVE-2021-26707 | `11e5dd56de8a` | 2021-01-04 | 2021-06-02 | eval | verified | core |
| F3-24 | immerjs/immer | CVE-2020-28477 | `da2bd4fa0edc` | 2021-01-20 | 2021-01-19 | eval | verified | core |
| F3-25 | lukeed/dset | CVE-2020-28277 | `a4b8a935031b` | 2021-01-27 | 2020-12-29 | eval | verified | core |
| F3-26 | swordev/merge | CVE-2020-28499 | `7b0ddc2701d8` | 2021-02-22 | 2021-02-18 | eval | verified | core |
| F3-27 | mout/mout | CVE-2020-7792 | `3fecf1333e6d` | 2021-07-15 | 2020-12-11 | eval | verified | core |
| F3-28 | mariocasciaro/object-path | CVE-2021-23434 | `7bdf4abefd10` | 2021-08-27 | 2021-08-27 | eval | verified | core |
| F3-29 | jonschlinkert/set-value | CVE-2021-23440 | `383b72d47c74` | 2021-08-30 | 2021-09-12 | eval | verified | core |
| F3-30 | immerjs/immer | CVE-2021-23436 | `fa671e55ee9b` | 2021-08-31 | 2021-09-01 | eval | verified | core |
| F3-31 | mariocasciaro/object-path | CVE-2021-3805 | `4f0903fd7c83` | 2021-09-16 | 2021-09-17 | eval | verified | core |
| F3-32 | janl/node-jsonpointer | CVE-2021-23807 | `a0345f3550cd` | 2021-10-31 | 2021-11-03 | eval | verified | core |
| F3-33 | ljharb/qs | CVE-2022-24999 | `8b4cc14cda94` | 2021-12-28 | 2022-11-26 | eval | verified | core |
| F3-34 | manuelstofer/json-pointer | CVE-2021-23820, CVE-2022-4742 | `859c9984b6c4` | 2022-02-17 | 2021-11-03 | eval | verified | core |
| F3-35 | minimistjs/minimist | CVE-2021-44906 | `c2b981977fa8` | 2022-03-22 | 2022-03-17 | eval | verified | core |
| F3-36 | lukeed/dset | CVE-2022-25645 | `2d156c7f6158` | 2022-05-03 | 2022-05-01 | eval | verified | core |
| F3-37 | protobufjs/protobuf.js | CVE-2022-25878 | `3357ef753871` | 2022-05-20 | 2022-05-27 | eval | verified | core |
| F3-38 | mout/mout | CVE-2022-21213 | `17ffdc2a9641` | 2022-09-19 | 2022-06-17 | eval | verified | core |
| F3-39 | json5/json5 | CVE-2022-46175 | `7774c1097993` | 2022-12-16 | 2022-12-24 | eval | verified | core |
| F3-40 | protobufjs/protobuf.js | CVE-2023-36665 | `e66379f451b0` | 2023-06-23 | 2023-07-05 | eval | verified | core |
| F3-41 | lukeed/dset | CVE-2024-21529 | `16d6154e085b` | 2024-09-09 | 2024-09-11 | eval | verified | core |
| F3-42 | lodash/lodash | CVE-2025-13465 | `edadd452146f` | 2025-12-05 | 2026-01-21 | eval | verified | core |

**Same-repository recurrences** (verified; arrow marks the cutoff):

- lodash/lodash: F3-02 (2018-01, memory) F3-06 (2018-08, memory) F3-11 (2019-06, memory) F3-17 (2020-07, memory) → T → F3-42 (2025-12, eval)
- lukeed/dset: F3-25 (2021-01, eval) F3-36 (2022-05, eval) F3-41 (2024-09, eval)
- mariocasciaro/object-path: F3-20 (2020-10, memory) → T → F3-28 (2021-08, eval) F3-31 (2021-09, eval)
- hapijs/hoek: F3-03 (2018-02, memory) F3-13 (2020-02, straddle)
- immerjs/immer: F3-24 (2021-01, eval) F3-30 (2021-08, eval)
- jonschlinkert/merge-deep: F3-04 (2018-02, memory) → T → F3-23 (2021-01, eval)
- jonschlinkert/set-value: F3-10 (2019-06, memory) → T → F3-29 (2021-08, eval)
- ljharb/qs: F3-01 (2017-02, memory) → T → F3-33 (2021-12, eval)
- manuelstofer/json-pointer: F3-19 (2020-09, memory) → T → F3-34 (2022-02, eval)
- minimistjs/minimist: F3-15 (2020-03, memory) → T → F3-35 (2022-03, eval)
- mout/mout: F3-27 (2021-07, eval) F3-38 (2022-09, eval)
- protobufjs/protobuf.js: F3-37 (2022-05, eval) F3-40 (2023-06, eval)
- swordev/merge: F3-07 (2018-10, memory) → T → F3-26 (2021-02, eval)

**Pairs across the cutoff:**

- Same-repo pairs: 9 of 20 eval instances have at least one memory instance in the same repository: F3-23 (jonschlinkert/merge-deep), F3-26 (swordev/merge), F3-28 (mariocasciaro/object-path), F3-29 (jonschlinkert/set-value), F3-31 (mariocasciaro/object-path), F3-33 (ljharb/qs), F3-34 (manuelstofer/json-pointer), F3-35 (minimistjs/minimist), F3-42 (lodash/lodash).
- Cross-repo pairs: each eval instance has between 16 and 20 memory instances from other repositories (between 0 and 0 in another language family; TypeScript counted with JavaScript).
- Eval instances that can only be matched cross-repo: 11.
- Memory instances: 20; straddle instances: F3-13, F3-18.

**Notable:**

- lodash/lodash: the same safeGet helper was patched three times (2018 __proto__, 2018 prototype, 2019 constructor), then baseSet (2020) and baseUnset (2025).
- Type-confusion bypass: checks compared path segments to strings with ===, so an array segment like ['__proto__'] passed. Seen in object-path, set-value and immer (2021), json-pointer and mout (2022), dset (2024).
- Blocked-key lists that grew one key at a time: merge-deep (__proto__ 2018, constructor/prototype 2021), minimist (__proto__ 2020, constructor 2022), protobufjs (__proto__ 2022, prototype 2023), hoek (merge 2018, clone 2020).
- The GHSA for dset CVE-2020-28277 links an unrelated 2018 commit; the real fix is from 2021-01-27. The minimist 0.2.4 backport shipped an operator-precedence bug in its new check, corrected in 2023.
- All F3 instances are JavaScript/TypeScript, so cross-language transfer cannot be tested on this family.

## F4: HTTP/1.1 server parses message framing leniently (Content-Length, Transfer-Encoding, line endings, header-name syntax), letting a front proxy and the server disagree on request boundaries (request smuggling)

16 verified of 16 listed; 8 memory, 8 eval, 0 straddle; 6 repositories; fit 'core' for 16.

| ID | Repo | Advisory | Fix commit | Fix date | Advisory date | Split | Status | Fit |
|---|---|---|---|---|---|---|---|---|
| F4-01 | netty/netty | CVE-2019-16869 | `39cafcb05c99` | 2019-09-20 | 2019-09-26 | memory | verified | core |
| F4-02 | netty/netty | CVE-2019-20444 | `a7c18d44b46e` | 2019-12-11 | 2020-01-29 | memory | verified | core |
| F4-03 | netty/netty | CVE-2019-20445, CVE-2020-7238 | `8494b046ec7e` | 2019-12-13 | 2020-01-27 | memory | verified | core |
| F4-04 | Pylons/waitress | CVE-2019-16785 | `8eba394ad75d` | 2019-12-19 | 2019-12-20 | memory | verified | core |
| F4-05 | Pylons/waitress | CVE-2019-16792 | `575994cd42e8` | 2019-12-19 | 2019-12-20 | memory | verified | core |
| F4-06 | Pylons/waitress | CVE-2019-16786 | `8ecd8dc4be00` | 2019-12-19 | 2019-12-20 | memory | verified | core |
| F4-07 | Pylons/waitress | CVE-2019-16789 | `ddb65b489d01` | 2019-12-24 | 2019-12-26 | memory | verified | core |
| F4-08 | puma/puma | CVE-2020-11076 | `eeff5668869b` | 2020-05-18 | 2020-05-22 | memory | verified | core |
| F4-09 | hyperium/hyper | CVE-2021-21299 | `8f93123efef5` | 2021-02-05 | 2021-02-11 | eval | verified | core |
| F4-10 | hyperium/hyper | CVE-2021-32715 | `1fb719e0b61a` | 2021-07-07 | 2021-07-07 | eval | verified | core |
| F4-11 | puma/puma | CVE-2021-41136 | `acdc3ae571df` | 2021-10-12 | 2021-10-12 | eval | verified | core |
| F4-12 | netty/netty | CVE-2021-43797 | `07aa6b5938a8` | 2021-12-09 | 2021-12-09 | eval | verified | core |
| F4-13 | Pylons/waitress | CVE-2022-24761 | `9e0b8c801e4d` | 2022-03-16 | 2022-03-17 | eval | verified | core |
| F4-14 | puma/puma | CVE-2023-40175 | `690155e7d644` | 2023-08-18 | 2023-08-18 | eval | verified | core |
| F4-15 | aio-libs/aiohttp | CVE-2023-47627 | `d5c12ba89055` | 2023-10-06 | 2023-11-14 | eval | verified | core |
| F4-16 | benoitc/gunicorn | CVE-2024-1135 | `ac29c9b0a758` | 2023-12-15 | 2024-04-16 | eval | verified | core |

**Same-repository recurrences** (verified; arrow marks the cutoff):

- Pylons/waitress: F4-04 (2019-12, memory) F4-05 (2019-12, memory) F4-06 (2019-12, memory) F4-07 (2019-12, memory) → T → F4-13 (2022-03, eval)
- netty/netty: F4-01 (2019-09, memory) F4-02 (2019-12, memory) F4-03 (2019-12, memory) → T → F4-12 (2021-12, eval)
- puma/puma: F4-08 (2020-05, memory) → T → F4-11 (2021-10, eval) F4-14 (2023-08, eval)
- hyperium/hyper: F4-09 (2021-02, eval) F4-10 (2021-07, eval)

**Pairs across the cutoff:**

- Same-repo pairs: 4 of 8 eval instances have at least one memory instance in the same repository: F4-11 (puma/puma), F4-12 (netty/netty), F4-13 (Pylons/waitress), F4-14 (puma/puma).
- Cross-repo pairs: each eval instance has between 4 and 8 memory instances from other repositories (between 4 and 8 in another language family; TypeScript counted with JavaScript).
- Eval instances that can only be matched cross-repo: 4.
- Memory instances: 8; straddle instances: none.

**Notable:**

- Pylons/waitress: four advisories within two weeks (Dec 2019 to Jan 2020), then CVE-2022-24761: the 2019 fix rejected values int() refused, but int() also accepts '+10'. hyper (CVE-2021-32715) and aiohttp (CVE-2023-47627) had the same lenient-integer root cause.
- netty/netty: whitespace before the colon (2019), declared incompletely fixed by CVE-2020-7238, then missing colon, Content-Length plus chunked, and control characters around header names (2021), all in the same header-splitting code.
- puma's 2020 fix accepted chunked anywhere in a Transfer-Encoding list; hyper (2021) and gunicorn (2024) fixes insist that chunked must be the last coding.

## Candidates looked at and left out

- F1 curl/curl (CVE-2024-11053, CVE-2025-0167): Credential leak on redirect caused by .netrc parser flaws (fix commits e9b9bbac22c26cf67316fa8e6c6b9e831af31949, 9fce2c55d4b0273ac99b59bd8cb982a6d96b88cf, 9bee39bfed2c413b4cc4eb306a57ac92a1854907, 0e120c5b925e8ca75d5319e319e5ce4b8080d8eb were fetched). The diffs fix netrc parsing, not the redirect check, so the lesson would not transfer; left out to keep the family crisp.
- F1 golang/go (no advisory): Commit 3f9d49f9e3df56a168312a2863fc9461da3d6b8f (2026-06-04, 'use raw Punycode when deciding if we should copy headers on redirect') is a real recurrence of the Go redirect bug, but no advisory references it (GO-2026-5026 is about x/net/idna).
- F1 denoland/deno (no advisory): Commits fbe07f1a79d4bd8142ada44b562c8dd14e005149 and 131a72736f59fb00185b1974806f5ad8ede46717 (July 2026) fix further redirect header issues, but no advisory was found for them.
- F1 httpie/cli (CVE-2022-24737): Cookies forwarded to third parties on redirect; the linked fix 65ab7d5caaaf2f95e61f9dd65441801c2ddee38b is a 30-file feature commit (new session cookie format) where the fix is buried.
- F1 ethanent/phin (GHSA-x565-32qp-m3vf): Linked fix commit c071f95336a987dad9332fd388adeb249925cc57 returns 404 on GitHub.
- F1 guzzle/guzzle (CVE-2022-29248, CVE-2026-67339): Not checked in depth: CVE-2022-29248 is cookie-jar domain matching, CVE-2026-67339 sends Proxy-Authorization to origins outside a redirect context.
- F1 various (CVE-2026-41715, CVE-2026-85717, CVE-2026-107282, CVE-2026-55553, CVE-2026-49336, CVE-2026-103030, CVE-2026-88013, CVE-2026-55403, CVE-2026-67435, CVE-2026-59180, CVE-2026-32913, CVE-2026-53840, GHSA-9857-6mw7-fq2m, GHSA-8mxv-9xhp-86h4): Further 2026 advisories of the same family found in the GitHub database (reactor-netty, async-http-client, urllib (npm), kiota, dio, rclone, datamodel-code-generator, linuxfabrik-lib, apprise, openclaw, gix-transport) but not fetched or verified for lack of time. They would only add to the evaluation side.
- F2 mholt/archiver (CVE-2025-3445): No fix: the advisory marks no patched version and its only commit link (fea250ac6eacd56f90a82fbe2481cfdbb9a1bbd1) edits the README.
- F2 cthackers/adm-zip (CVE-2026-76845): No patched version (destination symlinks followed); linked PR #575 not merged into a release.
- F2 kevva/decompress (CVE-2026-10732, CVE-2026-39243): Upstream is unmaintained and has no patched version; the maintained fork's fix is listed as CVE-2026-53486.
- F2 max-mapper/extract-zip (CVE-2026-56876, CVE-2026-19693): No patched version.
- F2 icsharpcode/SharpZipLib (CVE-2021-32842): FastZip base-directory prefix flaw introduced by the 2018 fix; no commit in v1.3.2...v1.3.3 touches FastZip or WindowsNameTransform, so no verifiable fix commit.
- F2 srikanth-lingala/zip4j (CVE-2018-1002202): Advisory has no fix link and no fix commit was located.
- F2 hashicorp/go-getter (advisory ids not collected): Several archive/symlink advisories (2022, 2025) not examined for lack of time.
- F3 dojo/dojo (CVE-2021-23450): No patched version (setObject).
- F3 protobufjs/protobuf.js (CVE-2026-59876): Text-format map parsing mutates the returned map's prototype (2026); not fetched or verified.

## Caveats

- Several primary commits are merge commits (PR merges or 'Merge commit from fork'); their diff against the first parent is the whole fix. Squash or backport commits are listed next to them.
- Two primaries are only on release branches (rest-client 1.8.x, scrapy 2.11); `on_default_branch` is recorded for every commit.
- Test files are classified by path heuristics (see `method.test_files` in the JSON). Some fixes have no test change at all (curl 2022, tar-fs, adm-zip, several jonschlinkert packages).
- Some diffs are noisy: dist/ rebuilds (jszip, lodash 2025, swordev/merge), lockfiles (mout 2022), reformatting (object-path 2020-2021), very large feature diffs (cpython PEP 706).
- Fixed versions come from the advisories; where an advisory range and its text disagree, both are noted.
- Repository names are current GitHub names. Renamed or moved: psf/requests (was requests/requests), isaacs/node-tar (was npm/node-tar), composefs/tar-rs (was alexcrichton/tar-rs), swordev/merge (was yeikos/js.merge); minimistjs/minimist continues the deleted substack/minimist; actions/http-client, npm/fstream, haf/DotNetZip.Semverd and mholt/archiver are archived (still readable).
