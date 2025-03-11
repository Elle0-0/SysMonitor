from pyngrok import ngrok

# Set your ngrok authentication token
ngrok.set_auth_token("HIDDEN")

# Open a HTTP tunnel on the specified port
http_tunnel = ngrok.connect(65433)
print("Public URL:", http_tunnel.public_url)

# Keep the script running
input("Press Enter to exit...")