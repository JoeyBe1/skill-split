# skill-split Dockerfile
# Multi-stage build for optimal image size

FROM python:3.13-slim as builder

LABEL maintainer="skill-split contributors"
LABEL description="Progressive disclosure for AI documentation"

# Set working directory
WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY pyproject.toml ./
COPY README.md ./

RUN pip install --no-cache-dir --user .

# Runtime stage
FROM python:3.13-slim

LABEL maintainer="skill-split contributors"
LABEL description="Progressive disclosure for AI documentation"

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /root/.local /root/.local

# Make sure scripts in .local are usable
ENV PATH=/root/.local/bin:$PATH

# Set working directory
WORKDIR /data

# Copy source code
COPY core/ ./core/
COPY handlers/ ./handlers/
COPY models.py ./
COPY skill_split.py ./

# Create volume for database
VOLUME ["/data"]

# Default command
ENTRYPOINT ["python", "skill_split.py"]
CMD ["--help"]

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "from core.database import Database; db = Database(); exit(0 if db.conn else 1)"

# Metadata
ARG VERSION=1.0.0
ARG BUILD_DATE
ARG VCS_REF

LABEL org.opencontainers.image.title="skill-split"
LABEL org.opencontainers.image.description="Split YAML and Markdown files into searchable SQLite sections"
LABEL org.opencontainers.image.version="${VERSION}"
LABEL org.opencontainers.image.created="${BUILD_DATE}"
LABEL org.opencontainers.image.revision="${VCS_REF}"
LABEL org.opencontainers.image.authors="skill-split contributors"
LABEL org.opencontainers.image.url="https://github.com/user/skill-split"
LABEL org.opencontainers.image.source="https://github.com/user/skill-split"
