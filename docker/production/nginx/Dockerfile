# based on https://github.com/umputun/nginx-le
FROM nginx:1.17.6-alpine

ADD ./docker/production/nginx/nginx.conf /etc/nginx/nginx.conf
ADD ./docker/production/nginx/service.conf /etc/nginx/service.conf

ADD ./docker/production/nginx/entrypoint.sh /entrypoint.sh
ADD ./docker/production/nginx/le.sh /le.sh

RUN \
 rm /etc/nginx/conf.d/default.conf && \
 chmod +x /entrypoint.sh && \
 chmod +x /le.sh && \
 apk add  --update certbot tzdata openssl && \
 rm -rf /var/cache/apk/*

CMD ["/entrypoint.sh"]
