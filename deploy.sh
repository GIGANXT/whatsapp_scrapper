#!/bin/bash

# Update system packages
sudo apt-get update
sudo apt-get upgrade -y

# Install required system packages
sudo apt-get install -y python3-pip python3-venv nginx supervisor

# Create application directory in root
sudo mkdir -p /root/whatsapp-scraping
cd /root/whatsapp-scraping

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
pip install gunicorn

# Create Nginx configuration
sudo tee /etc/nginx/sites-available/whatsapp-scraping << EOF
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:3232;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

# Enable Nginx configuration
sudo ln -s /etc/nginx/sites-available/whatsapp-scraping /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx

# Create Supervisor configuration
sudo tee /etc/supervisor/conf.d/whatsapp-scraping.conf << EOF
[program:whatsapp-scraping]
directory=/root/whatsapp-scraping
command=/root/whatsapp-scraping/venv/bin/gunicorn -c gunicorn_config.py wsgi:app
user=root
autostart=true
autorestart=true
stderr_logfile=/var/log/whatsapp-scraping.err.log
stdout_logfile=/var/log/whatsapp-scraping.out.log
environment=PYTHONPATH="/root/whatsapp-scraping"
EOF

# Reload Supervisor
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start whatsapp-scraping

# Create .env file
sudo tee /root/whatsapp-scraping/.env << EOF
PORT=3232
FLASK_ENV=production
FLASK_APP=app.py
EOF

# Set proper permissions
sudo chown -R root:root /root/whatsapp-scraping
sudo chmod -R 755 /root/whatsapp-scraping

echo "Deployment completed! Your application should be running at http://your-server-ip" 