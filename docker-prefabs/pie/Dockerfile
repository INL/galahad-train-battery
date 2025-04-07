ARG VERSION=dev
ARG CPU_GPU=cpu

FROM instituutnederlandsetaal/galahad-taggers:$CPU_GPU-$VERSION

ENV CPU_GPU=$CPU_GPU

COPY --link .  ./
RUN uv --no-cache pip install --system --index-strategy=unsafe-best-match --no-deps --no-cache-dir -r requirements.txt && uv cache clean
