@echo off
echo Testing HTTP and HTTPS requests through Ship Proxy...
echo --------------------------------------------

REM Test HTTP - example.com
echo 1. HTTP: http://example.com
curl -x http://localhost:8080 http://example.com
echo --------------------------------------------

REM Test HTTP - neverssl.com
echo 2. HTTP: http://neverssl.com
curl -x http://localhost:8080 http://neverssl.com
echo --------------------------------------------

REM Test HTTP - example.com
echo 3. HTTP: http://example.com
curl -x http://localhost:8080 http://example.com
echo --------------------------------------------

REM Test HTTPS - example.com
echo 4. HTTPS: https://example.com
curl -x http://localhost:8080 https://example.com
echo --------------------------------------------

REM Test HTTP - neverssl.com
echo 5. HTTP: http://neverssl.com
curl -x http://localhost:8080 http://neverssl.com
echo --------------------------------------------

REM Test HTTPS - example.com
echo 6. HTTPS: https://example.com
curl -x http://localhost:8080 https://example.com
echo --------------------------------------------


echo All tests completed.
pause
