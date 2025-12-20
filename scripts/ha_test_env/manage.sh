#!/bin/bash
# Shure SLX-D Home Assistant Test Environment Management Script
#
# Usage:
#   ./manage.sh start     - Start HA test instance with mock server
#   ./manage.sh stop      - Stop all containers
#   ./manage.sh restart   - Restart all containers
#   ./manage.sh logs      - Show logs (follow mode)
#   ./manage.sh status    - Check container status
#   ./manage.sh shell     - Open shell in HA container
#   ./manage.sh clean     - Stop and remove all data (fresh start)
#   ./manage.sh setup     - Configure integration via API
#   ./manage.sh entities  - List all integration entities
#   ./manage.sh test      - Run full test cycle

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Configuration
HA_URL="http://localhost:8123"
MOCK_HOST="mock_slxd"
MOCK_PORT="2202"
INTEGRATION_DOMAIN="shure_slxd"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_debug() {
    echo -e "${BLUE}[DEBUG]${NC} $1"
}

wait_for_ha() {
    log_info "Waiting for Home Assistant to start..."
    local max_attempts=60
    local attempt=1

    while [ $attempt -le $max_attempts ]; do
        if curl -s "$HA_URL/api/" > /dev/null 2>&1; then
            log_info "Home Assistant is ready!"
            return 0
        fi
        echo -n "."
        sleep 2
        attempt=$((attempt + 1))
    done

    echo ""
    log_error "Home Assistant did not start within expected time"
    return 1
}

wait_for_mock() {
    log_info "Waiting for Mock SLX-D server to start..."
    local max_attempts=30
    local attempt=1

    while [ $attempt -le $max_attempts ]; do
        if nc -z localhost 2202 2>/dev/null; then
            log_info "Mock SLX-D server is ready!"
            return 0
        fi
        echo -n "."
        sleep 1
        attempt=$((attempt + 1))
    done

    echo ""
    log_error "Mock SLX-D server did not start within expected time"
    return 1
}

cmd_start() {
    log_info "Starting Shure SLX-D test environment..."

    # Check if Docker is running
    if ! docker info > /dev/null 2>&1; then
        log_error "Docker is not running. Please start Docker first."
        exit 1
    fi

    # Create directories if needed
    mkdir -p config

    # Build and start containers
    log_info "Building containers..."
    docker compose build

    log_info "Starting containers..."
    docker compose up -d

    wait_for_mock
    wait_for_ha

    echo ""
    log_info "=============================================="
    log_info "Environment is ready!"
    log_info "=============================================="
    log_info "Home Assistant: $HA_URL"
    log_info "Mock SLX-D:     localhost:2202"
    echo ""
    log_info "To add the integration, run: ./manage.sh setup"
    log_info "To view logs, run: ./manage.sh logs"
}

cmd_stop() {
    log_info "Stopping test environment..."
    docker compose down
    log_info "Environment stopped"
}

cmd_restart() {
    log_info "Restarting test environment..."
    docker compose restart
    wait_for_mock
    wait_for_ha
    log_info "Environment restarted"
}

cmd_logs() {
    local service="${2:-}"
    if [ -n "$service" ]; then
        log_info "Showing logs for $service (Ctrl+C to exit)..."
        docker compose logs -f "$service"
    else
        log_info "Showing all logs (Ctrl+C to exit)..."
        docker compose logs -f
    fi
}

cmd_status() {
    echo ""
    log_info "Container Status:"
    docker compose ps
    echo ""

    if curl -s "$HA_URL/api/" > /dev/null 2>&1; then
        log_info "Home Assistant API: RESPONDING"
    else
        log_warn "Home Assistant API: NOT RESPONDING"
    fi

    if nc -z localhost 2202 2>/dev/null; then
        log_info "Mock SLX-D Server:  RESPONDING"
    else
        log_warn "Mock SLX-D Server:  NOT RESPONDING"
    fi
}

cmd_shell() {
    log_info "Opening shell in Home Assistant container..."
    docker exec -it ha_slxd_test /bin/bash
}

cmd_clean() {
    log_warn "This will remove all Home Assistant data. Are you sure? (y/N)"
    read -r response
    if [ "$response" = "y" ] || [ "$response" = "Y" ]; then
        log_info "Stopping and cleaning up..."
        docker compose down -v 2>/dev/null || true
        rm -rf config/.storage config/home-assistant_v2.db config/home-assistant.log* config/.HA_VERSION
        log_info "Cleanup complete. Run './manage.sh start' for a fresh instance."
    else
        log_info "Cancelled"
    fi
}

cmd_setup() {
    log_info "Setting up Shure SLX-D integration via REST API..."

    # Check if HA is running
    if ! curl -s "$HA_URL/api/" > /dev/null 2>&1; then
        log_error "Home Assistant is not running. Start it first with: ./manage.sh start"
        exit 1
    fi

    # Check if integration is already configured
    log_debug "Checking for existing configuration..."
    EXISTING=$(curl -s "$HA_URL/api/config/config_entries/entry" | python3 -c "
import sys, json
entries = json.load(sys.stdin)
for entry in entries:
    if entry.get('domain') == '$INTEGRATION_DOMAIN':
        print(entry['entry_id'])
        break
" 2>/dev/null || echo "")

    if [ -n "$EXISTING" ]; then
        log_warn "Integration is already configured (entry_id: $EXISTING)"
        log_info "To reconfigure, remove it first in HA UI or run ./manage.sh clean"
        return 0
    fi

    # Start config flow
    log_info "Starting config flow..."
    FLOW_RESULT=$(curl -s -X POST "$HA_URL/api/config/config_entries/flow" \
        -H "Content-Type: application/json" \
        -d "{\"handler\": \"$INTEGRATION_DOMAIN\"}")

    FLOW_ID=$(echo "$FLOW_RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('flow_id', ''))" 2>/dev/null)

    if [ -z "$FLOW_ID" ]; then
        log_error "Failed to start config flow"
        log_debug "Response: $FLOW_RESULT"
        exit 1
    fi

    log_debug "Flow ID: $FLOW_ID"

    # Submit host configuration
    log_info "Submitting connection details..."
    STEP_RESULT=$(curl -s -X POST "$HA_URL/api/config/config_entries/flow/$FLOW_ID" \
        -H "Content-Type: application/json" \
        -d "{\"host\": \"$MOCK_HOST\", \"port\": $MOCK_PORT}")

    RESULT_TYPE=$(echo "$STEP_RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('type', ''))" 2>/dev/null)

    if [ "$RESULT_TYPE" = "create_entry" ]; then
        ENTRY_TITLE=$(echo "$STEP_RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('title', ''))" 2>/dev/null)
        log_info "Integration configured successfully!"
        log_info "Device: $ENTRY_TITLE"
    elif [ "$RESULT_TYPE" = "form" ]; then
        STEP_ID=$(echo "$STEP_RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('step_id', ''))" 2>/dev/null)
        log_warn "Config flow requires additional step: $STEP_ID"
        log_debug "Response: $STEP_RESULT"
    else
        log_error "Setup failed with result type: $RESULT_TYPE"
        log_debug "Response: $STEP_RESULT"
        exit 1
    fi

    # Wait for entities to be created
    log_info "Waiting for entities to be created..."
    sleep 5

    cmd_entities
}

cmd_entities() {
    log_info "Fetching integration entities..."

    if ! curl -s "$HA_URL/api/" > /dev/null 2>&1; then
        log_error "Home Assistant is not running"
        exit 1
    fi

    echo ""
    curl -s "$HA_URL/api/states" | python3 -c "
import sys, json
states = json.load(sys.stdin)
entities = [s for s in states if 'shure' in s['entity_id'].lower() or 'slxd' in s['entity_id'].lower()]
if not entities:
    print('No Shure SLX-D entities found. Run ./manage.sh setup first.')
else:
    print(f'Found {len(entities)} entities:')
    print('-' * 60)
    for s in sorted(entities, key=lambda x: x['entity_id']):
        state = s['state']
        unit = s.get('attributes', {}).get('unit_of_measurement', '')
        print(f'{s[\"entity_id\"]}: {state} {unit}')
"
}

cmd_test() {
    log_info "Running full test cycle..."

    cmd_start
    sleep 5
    cmd_setup

    log_info "Waiting for data collection..."
    sleep 15

    # Check for errors in logs
    log_info "Checking logs for errors..."
    if docker compose logs homeassistant 2>&1 | grep -iE "error|exception" | grep -i "shure\|slxd" | head -5; then
        log_warn "Found potential errors in logs (see above)"
    else
        log_info "No obvious errors found"
    fi

    echo ""
    cmd_entities

    echo ""
    log_info "Test cycle complete."
    log_info "Home Assistant running at: $HA_URL"
}

# Main command handler
case "${1:-}" in
    start)    cmd_start ;;
    stop)     cmd_stop ;;
    restart)  cmd_restart ;;
    logs)     cmd_logs "$@" ;;
    status)   cmd_status ;;
    shell)    cmd_shell ;;
    clean)    cmd_clean ;;
    setup)    cmd_setup ;;
    entities) cmd_entities ;;
    test)     cmd_test ;;
    *)
        echo "Shure SLX-D Home Assistant Test Environment"
        echo ""
        echo "Usage: $0 <command>"
        echo ""
        echo "Commands:"
        echo "  start     Start Home Assistant with mock SLX-D server"
        echo "  stop      Stop all containers"
        echo "  restart   Restart all containers"
        echo "  logs      Show logs (follow mode). Use 'logs mock_slxd' for specific service"
        echo "  status    Check container and service status"
        echo "  shell     Open shell in Home Assistant container"
        echo "  clean     Stop and remove all data (fresh start)"
        echo "  setup     Configure integration via REST API"
        echo "  entities  List all integration entities"
        echo "  test      Run full test cycle"
        ;;
esac
