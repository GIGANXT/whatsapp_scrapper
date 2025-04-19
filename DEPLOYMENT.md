# Deployment Guide for Hostinger VPS

## Prerequisites
- Hostinger VPS with Ubuntu OS
- SSH access to your VPS
- Root access to the server

## Deployment Steps

1. **Connect to your VPS**
   ```bash
   ssh root@your-server-ip
   ```

2. **Upload your application files**
   You need to upload the following files to your VPS:
   - app.py
   - requirements.txt
   - gunicorn_config.py
   - wsgi.py
   - deploy.sh

   You can use SCP or SFTP to upload these files. For example:
   ```bash
   scp -r /path/to/local/whatsapp-scraping/* root@your-server-ip:/root/whatsapp-scraping/
   ```

3. **Make the deployment script executable**
   ```bash
   chmod +x deploy.sh
   ```

4. **Run the deployment script**
   ```bash
   ./deploy.sh
   ```

5. **Verify the deployment**
   - Check if Nginx is running:
     ```bash
     sudo systemctl status nginx
     ```
   - Check if Supervisor is running your application:
     ```bash
     sudo supervisorctl status
     ```
   - Check the application logs:
     ```bash
     tail -f /var/log/whatsapp-scraping.out.log
     ```

6. **Access your application**
   Your application should be accessible at:
   ```
   http://your-server-ip
   ```

## Important Notes

1. **Security**
   - Make sure your VPS firewall is properly configured
   - Consider setting up SSL/HTTPS using Let's Encrypt
   - Keep your system and packages updated

2. **Maintenance**
   - To restart the application:
     ```bash
     sudo supervisorctl restart whatsapp-scraping
     ```
   - To check application status:
     ```bash
     sudo supervisorctl status whatsapp-scraping
     ```
   - To view logs:
     ```bash
     tail -f /var/log/whatsapp-scraping.out.log
     ```

3. **Backup**
   - Regularly backup your application data
   - Consider setting up automated backups

## Troubleshooting

1. If the application is not accessible:
   - Check Nginx status: `sudo systemctl status nginx`
   - Check Supervisor status: `sudo supervisorctl status`
   - Check logs: `tail -f /var/log/whatsapp-scraping.err.log`

2. If you need to make changes:
   - Update your files
   - Restart the application: `sudo supervisorctl restart whatsapp-scraping`

3. If you need to update dependencies:
   - Activate virtual environment: `source /root/whatsapp-scraping/venv/bin/activate`
   - Install new dependencies: `pip install -r requirements.txt`
   - Restart the application: `sudo supervisorctl restart whatsapp-scraping` 