## Para configurar las variables de entorno
1. Copiar las variables de entorno en el cortapapeles.
2. vim .env
3. Shift + Ctrl + V
4. :wq + Enter

## Para pegar configuración presente en nginx.conf
Asumimos primero que existe el nombre de dominio appnau.com en Route53, que el dominio apunta a una Elastic IP, y que la Elastic IP está asociada a la instancia EC2 donde se encuentra el proyecto.

1. Copiar configuración presente en el archivo nginx.conf en el cortapapeles.
2. sudo vim /etc/nginx/sites-available/nauai
3. Shift + Ctrl + V
4. :wq + Enter
5. sudo vim /etc/nginx/nginx.conf, e incorporar dentro del header http: limit_req_zone $binary_remote_addr zone=general:10m rate=30r/m;
6. If you want to change the configuration of the nginx.conf file, use: sudo systemctl reload nginx.

## Para dejar servicio corriendo
1. sudo vim /etc/systemd/system/nauai.service
2. Pegar la configuración incluida en nauai.service.
3. sudo systemctl daemon-reload
4. sudo systemctl enable nauai
5. sudo systemctl start nauai
6. sudo systemctl status nauai