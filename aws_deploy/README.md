## Para configurar las variables de entorno
1. Copiar las variables de entorno en el cortapapeles.
2. vim .env
3. Shift + Ctrl + V
4. :wq + Enter

## Para pegar configuración presente en nginx.conf
Asumimos primero que existe el nombre de dominio appnau.com en Route53, que el dominio apunta a una Elastic IP, y que la Elastic IP está asociada a la instancia EC2 donde se encuentra el proyecto.

1. Copiar configuración presente en el archivo nginx.conf en el cortapapeles.
2. vim /etc/nginx/sites-available/nauai
3. Shift + Ctrl + V
4. :wq + Enter