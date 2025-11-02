# Podman Setup Guide for WillGPT

This guide explains how to run WillGPT using Podman and podman-compose for local development and testing.

## Prerequisites

1. **Install Podman** (if not already installed):
   ```bash
   # macOS (using Homebrew)
   brew install podman

   # Linux (Fedora/RHEL)
   sudo dnf install podman podman-compose

   # Linux (Ubuntu/Debian)
   sudo apt-get install podman podman-compose
   ```

2. **Initialize Podman machine** (macOS only):
   ```bash
   podman machine init
   podman machine start
   ```

3. **Install podman-compose** (if not included):
   ```bash
   pip install podman-compose
   ```

## Quick Start

### 1. Build and Start Services

Start just the core services (Qdrant + app):
```bash
podman-compose up -d
```

Start with Jupyter notebook:
```bash
podman-compose --profile jupyter up -d
```

### 2. Check Service Health

```bash
# Check all running containers
podman ps

# Check Qdrant health
curl http://localhost:6333/health

# View logs
podman-compose logs -f qdrant
podman-compose logs -f willgpt-app
```

### 3. Access Services

- **Qdrant Web UI**: http://localhost:6333/dashboard
- **Qdrant REST API**: http://localhost:6333
- **Jupyter Lab**: http://localhost:8888 (if started with --profile jupyter)

## Usage Examples

### Run Commands in the App Container

```bash
# Enter the container shell
podman exec -it willgpt-app /bin/bash

# Inside the container:
python test_qdrant_connection.py
python test_parser.py data/raw/chatgpt.json
python merge_and_upload.py --yes
python retrieval/search_qdrant.py "your query"
```

### One-Line Commands

```bash
# Test Qdrant connection
podman exec willgpt-app python test_qdrant_connection.py

# Parse ChatGPT export
podman exec willgpt-app python test_parser.py data/raw/chatgpt.json

# Merge and upload all platforms
podman exec -it willgpt-app python merge_and_upload.py

# Search (interactive mode)
podman exec -it willgpt-app python retrieval/search_qdrant.py

# Search (single query)
podman exec willgpt-app python retrieval/search_qdrant.py "self-effacing patterns" --limit 10
```

## Data Management

### Adding Raw Data Files

Place your export files in the `data/raw/` directory on your host machine. They will be automatically available inside the container:

```bash
# Copy exports to data/raw/
cp ~/Downloads/chatgpt.json data/raw/
cp ~/Downloads/claude.json data/raw/
cp ~/Downloads/claude-projects.json data/raw/

# Verify files are accessible in container
podman exec willgpt-app ls -lh data/raw/
```

### Accessing Processed Data

Processed files are saved to `data/processed/` and are accessible both inside the container and on your host:

```bash
# View processed files
ls -lh data/processed/

# Inside container
podman exec willgpt-app ls -lh data/processed/
```

## Development Workflow

### Local Development with Hot Reload

The compose file mounts your source code as volumes, so changes are immediately reflected:

1. Edit code on your host machine (e.g., `parsers/chatgpt_parser.py`)
2. Run commands in the container to test changes
3. No need to rebuild the container

```bash
# Example: Test parser changes
vim parsers/chatgpt_parser.py
podman exec willgpt-app python test_parser.py data/raw/chatgpt.json
```

### Rebuilding After Dependency Changes

If you update `requirements.txt`:

```bash
# Rebuild the image
podman-compose build willgpt-app

# Restart services
podman-compose up -d
```

## Environment Configuration

### Using .env File

Create a `.env` file in the project root for environment variables:

```bash
# .env
QDRANT_API_KEY=your-cloud-api-key-if-needed
QDRANT_COLLECTION_NAME=will-gpt
```

The compose file automatically loads this file.

### Local vs Cloud Qdrant

**Local Qdrant (Default):**
- Automatically configured to use the containerized Qdrant service
- URL: `http://qdrant:6333` (internal container network)
- No API key needed
- Data persists in Docker volume `qdrant-storage`

**Cloud Qdrant:**
- Modify `.env` or environment variables in `podman-compose.yml`
- Set `QDRANT_URL=https://your-cluster.cloud.qdrant.io:6333`
- Set `QDRANT_API_KEY=your-api-key`

## Advanced Usage

### GPU Support (for embeddings)

Podman GPU support varies by platform. For GPU-accelerated embeddings:

**Option 1: Use Colab** (Recommended)
- Generate embeddings on Colab GPU as documented in CLAUDE.md
- Use local Qdrant for search/retrieval only

**Option 2: Podman with NVIDIA GPU** (Linux only)
```bash
# Install nvidia-container-toolkit
# Add to podman-compose.yml under willgpt-app:
#   devices:
#     - nvidia.com/gpu=all
```

**Option 3: Host GPU via Socket**
- Run embedding generation on host
- Store results in Qdrant container

### Jupyter Notebook Development

Start Jupyter service:
```bash
podman-compose --profile jupyter up -d

# Access at http://localhost:8888
# No password required (configured for local dev)
```

Run notebooks inside the container with access to local Qdrant:
- Open `notebooks/upload_to_qdrant_colab.ipynb`
- Change `QDRANT_URL` to `http://qdrant:6333`
- No API key needed for local instance

### Backing Up Qdrant Data

```bash
# Create a snapshot
curl -X POST "http://localhost:6333/collections/will-gpt/snapshots"

# Download snapshot
curl "http://localhost:6333/collections/will-gpt/snapshots/snapshot-name" --output backup.snapshot

# Restore snapshot (in container)
podman exec willgpt-app curl -X PUT "http://qdrant:6333/collections/will-gpt/snapshots/upload" \
  --data-binary @/path/to/backup.snapshot
```

## Troubleshooting

### Container Won't Start

```bash
# Check logs
podman-compose logs

# Rebuild from scratch
podman-compose down -v
podman-compose build --no-cache
podman-compose up -d
```

### Qdrant Connection Issues

```bash
# Check if Qdrant is healthy
podman exec willgpt-app curl http://qdrant:6333/health

# Check network connectivity
podman network inspect willgpt_default

# Restart Qdrant
podman-compose restart qdrant
```

### Permission Issues (SELinux)

On systems with SELinux (Fedora, RHEL), volume mounts need `:Z` flag (already configured):

```yaml
volumes:
  - ./data:/app/data:Z  # :Z sets appropriate SELinux labels
```

If you still have permission issues:
```bash
# Check SELinux status
getenforce

# Temporarily disable (not recommended for production)
sudo setenforce 0
```

### Out of Memory During Embedding

```bash
# Check container resource limits
podman stats willgpt-app

# Increase memory limit in podman-compose.yml:
#   deploy:
#     resources:
#       limits:
#         memory: 8G
```

For large datasets (23k+ chunks), use Colab GPU as recommended in CLAUDE.md.

## Stopping and Cleaning Up

### Stop Services

```bash
# Stop all services
podman-compose down

# Stop and remove volumes (DELETES QDRANT DATA)
podman-compose down -v
```

### Clean Up Resources

```bash
# Remove unused images
podman image prune

# Remove unused volumes
podman volume prune

# Remove everything (nuclear option)
podman system prune -a --volumes
```

## Production Considerations

This setup is optimized for **local development**. For production:

1. **Use Qdrant Cloud** instead of containerized Qdrant
2. **Add authentication** to Jupyter (remove `--NotebookApp.token=''`)
3. **Use proper secrets management** instead of .env files
4. **Enable HTTPS** with reverse proxy (nginx/traefik)
5. **Set resource limits** based on your deployment environment
6. **Use persistent volume drivers** for critical data
7. **Enable monitoring** (Prometheus + Grafana)

## Comparison: Podman vs Docker

This `podman-compose.yml` is compatible with Docker Compose with minimal changes:

```bash
# Using Docker instead of Podman
docker-compose up -d

# Or using Docker Compose V2
docker compose up -d
```

**Key Differences:**
- Podman runs rootless by default (better security)
- Podman uses `:Z` flag for SELinux volume labeling
- Podman machine required on macOS (like Docker Desktop)
- GPU support differs between platforms

## Additional Resources

- **Podman Documentation**: https://docs.podman.io/
- **Qdrant Documentation**: https://qdrant.tech/documentation/
- **Project Documentation**: See `CLAUDE.md` for full system architecture

## Quick Reference

```bash
# Start everything
podman-compose up -d

# View logs
podman-compose logs -f

# Execute commands
podman exec -it willgpt-app /bin/bash

# Stop everything
podman-compose down

# Rebuild after changes
podman-compose build && podman-compose up -d
```
