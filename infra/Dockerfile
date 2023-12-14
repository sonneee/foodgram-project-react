FROM nginx:1.19.3
COPY nginx.conf /etc/nginx/templates/default.conf
COPY ./frontend/build /usr/share/nginx/html/
COPY ./docs/.  /usr/share/nginx/html/api/docs/