# ---- Module 1 homework / Module 2 solution: web tier image -----------------
FROM nginx:1.27-alpine

# The stock image ships a default site that would shadow ours. Remove it.
RUN rm -f /etc/nginx/conf.d/default.conf

COPY nginx.conf /etc/nginx/conf.d/app.conf

EXPOSE 80

# wget ships with alpine, so no extra package needed here.
HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 \
    CMD wget -q -O /dev/null http://localhost/healthz || exit 1

# Inherited from the base image, shown for clarity: nginx must stay in the
# foreground. A daemonised process would exit and take the container with it.
CMD ["nginx", "-g", "daemon off;"]
