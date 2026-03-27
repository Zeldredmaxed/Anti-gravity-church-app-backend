import urllib.request
import urllib.error

url = "https://anti-gravity-church-app-backend-production.up.railway.app/api/v1/shorts/trending"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
try:
    response = urllib.request.urlopen(req)
    print("SUCCESS", response.status)
    print(response.read().decode('utf-8')[:500])
except urllib.error.HTTPError as e:
    print("ERROR", e.code)
    print(e.read().decode('utf-8'))
except Exception as e:
    print("OTHER ERROR", e)
