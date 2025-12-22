#!/usr/bin/env bash
# Deploy observability stack with proper initialization
# Usage: ./scripts/deploy-observability.sh [start|stop|restart|status]

set -euo pipefail

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$( dirname "$SCRIPT_DIR" )"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

log_success() {
    echo -e "${GREEN}✓${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
}

log_error() {
    echo -e "${RED}✗${NC} $1"
}

# Check if Docker is running
check_docker() {
    if ! docker info &> /dev/null; then
        log_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
    log_success "Docker is running"
}

# Create monitoring network
create_network() {
    log_info "Creating monitoring network..."
    if docker network inspect ai-monitoring &> /dev/null; then
        log_warn "Network ai-monitoring already exists"
    else
        docker network create ai-monitoring
        log_success "Created network ai-monitoring"
    fi
}

# Start observability stack
start_stack() {
    log_info "Starting observability stack..."
    
    cd "$PROJECT_ROOT"
    
    # Start observability services
    docker compose -f docker-compose.observability.yml up -d
    
    log_success "Observability stack started"
    
    log_info "Waiting for services to become healthy..."
    sleep 10
    
    # Check service health
    check_health
}

# Stop observability stack
stop_stack() {
    log_info "Stopping observability stack..."
    
    cd "$PROJECT_ROOT"
    docker compose -f docker-compose.observability.yml down
    
    log_success "Observability stack stopped"
}

# Restart observability stack
restart_stack() {
    log_info "Restarting observability stack..."
    stop_stack
    sleep 2
    start_stack
}

# Check service health
check_health() {
    local all_healthy=true
    
    # Check Prometheus
    if curl -sf http://localhost:9090/-/healthy &> /dev/null; then
        log_success "Prometheus is healthy"
    else
        log_error "Prometheus is not healthy"
        all_healthy=false
    fi
    
    # Check Loki
    if curl -sf http://localhost:3100/ready &> /dev/null; then
        log_success "Loki is healthy"
    else
        log_error "Loki is not healthy"
        all_healthy=false
    fi
    
    # Check Tempo
    if curl -sf http://localhost:3200/ready &> /dev/null; then
        log_success "Tempo is healthy"
    else
        log_error "Tempo is not healthy"
        all_healthy=false
    fi
    
    # Check Grafana
    if curl -sf http://localhost:3001/api/health &> /dev/null; then
        log_success "Grafana is healthy"
    else
        log_error "Grafana is not healthy"
        all_healthy=false
    fi
    
    # Check OTEL Collector
    if curl -sf http://localhost:13133 &> /dev/null; then
        log_success "OpenTelemetry Collector is healthy"
    else
        log_error "OpenTelemetry Collector is not healthy"
        all_healthy=false
    fi
    
    if [ "$all_healthy" = true ]; then
        echo ""
        log_success "All observability services are healthy"
        echo ""
        echo "Access points:"
        echo "  Grafana:    http://localhost:3001 (admin/admin)"
        echo "  Prometheus: http://localhost:9090"
        echo "  Loki:       http://localhost:3100"
        echo "  Tempo:      http://localhost:3200"
        echo ""
    else
        echo ""
        log_warn "Some services are not healthy. Check logs with:"
        echo "  docker compose -f docker-compose.observability.yml logs"
        return 1
    fi
}

# Show status
show_status() {
    cd "$PROJECT_ROOT"
    
    log_info "Observability stack status:"
    echo ""
    
    docker compose -f docker-compose.observability.yml ps
    
    echo ""
    log_info "Service health:"
    check_health || true
}

# Main
main() {
    local action="${1:-start}"
    
    echo "====================================="
    echo "  Observability Stack Deployment"
    echo "====================================="
    echo ""
    
    check_docker
    create_network
    
    case "$action" in
        start)
            start_stack
            ;;
        stop)
            stop_stack
            ;;
        restart)
            restart_stack
            ;;
        status)
            show_status
            ;;
        *)
            log_error "Unknown action: $action"
            echo "Usage: $0 [start|stop|restart|status]"
            exit 1
            ;;
    esac
}

main "$@"
