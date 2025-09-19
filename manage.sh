#!/bin/sh
set -e
# set -x  # Uncomment for debugging

# ==== BEGIN CONFIG ====
VERSION="0.1.0"
SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
ENV_FILE="$SCRIPT_DIR/.env"
DOCKER_COMPOSE_FILE="$SCRIPT_DIR/ops/docker-compose.yml"
ZENML_SERVER_URL="http://127.0.0.1:8237"
MLFLOW_SERVER_URL="http://127.0.0.1:5000"
SERVICE_STARTUP_DELAY=10
# ==== END CONFIG ====

# Format helpers
format_success() { printf "\033[1;32m%s\033[0m\n" "$1"; }
format_info()    { printf "\033[1;34m%s\033[0m\n" "$1"; }
format_warning() { printf "\033[1;33m%s\033[0m\n" "$1"; }
format_error()   { printf "\033[1;31m%s\033[0m\n" "$1"; }
format_bold()    { printf "\033[1m%s\033[0m\n" "$1"; }

# Logging helpers
log_success() { printf "%s %s\n" "$(format_success '[SUCCESS]')" "$1"; }
log_info()    { printf "%s %s\n" "$(format_info '[INFO]')" "$1"; }
log_warning()    { printf "%s %s\n" "$(format_warning '[WARNING]')" "$1"; }
log_error()   { printf "%s %s\n" "$(format_error '[ERROR]')" "$1" >&2; }

usage() {
    format_info "Clai engineering management script."
    format_info "Manage local infrastructure, settings, pipelines, and more."
    echo ""
    format_bold "Usage:"
    echo "  $(basename "$0") [options] <command> [command options]"
    echo ""
    format_bold "Options:"
    echo "  -h, --help              Show this help message"
    echo "  -v, --version           Show script version"
    echo ""
    format_bold "Commands:"
    echo "  infra                   Manage the infrastructure"
    echo "    --up                  Start the services"
    echo "    --down                Stop the services"
    echo "    --status              Status of services"
    echo ""
    echo "  settings                Manage ZenML settings"
    echo "    --export              Export local settings to ZenML secrets"
    echo "    --drop                Delete settings from ZenML secrets"
    echo ""
    echo "  pipeline                Run the given pipeline"
    echo "    --no-cache            Disable cache (optional)"
    echo "    --etl                 Run the ETL pipeline only"
    echo "    --rag                 Run the RAG pipeline only"
    echo "    --all                 Run all the pipelines"
    echo "    -c, --config FILE     Path to pipeline configuration file (required)"
}

# Infra command
manage_infra() {
    UP=0
    DOWN=0
    STATUS=0

    while [ $# -gt 0 ]; do
        case "$1" in
            --up) UP=1 ;;
            --down) DOWN=1 ;;
            --status) STATUS=1 ;;
            *)
                log_error "Unknown option for 'infra': $1"
                echo ""
                echo "Usage: $(basename "$0") infra [--up|--down|--status]"
                exit 1
                ;;
        esac
        shift
    done

    # Mutual exclusivity check
    if [ $UP -eq 1 ] && [ $DOWN -eq 1 ] || [ $UP -eq 1 ] && [ $STATUS -eq 1 ] || [ $DOWN -eq 1 ] && [ $STATUS -eq 1 ]; then
        log_error "Options --up, --down, and --status are mutually exclusive."
        exit 1
    elif [ $UP -eq 0 ] && [ $DOWN -eq 0 ] && [ $STATUS -eq 0 ]; then
        log_error "You must specify one of --up, --down, or --status."
        exit 1
    fi

    if [ $STATUS -eq 1 ]; then
        # Get all declared services
        DECLARED_SERVICES=$(docker compose --env-file "$ENV_FILE" -f "$DOCKER_COMPOSE_FILE" config --services)
        
        # Get currently running services
        RUNNING_SERVICES=$(docker compose --env-file "$ENV_FILE" -f "$DOCKER_COMPOSE_FILE" ps --services --status=running)
        
        ALL_RUNNING=1
        
        for SERVICE in $DECLARED_SERVICES; do
            FOUND=0
            for RUNNING in $RUNNING_SERVICES; do
                if [ "$SERVICE" = "$RUNNING" ]; then
                    FOUND=1
                    break
                fi
            done
            
            if [ $FOUND -eq 0 ]; then
                log_error "Service '$SERVICE' is not running."
                ALL_RUNNING=0
            fi
        done


        if [ $ALL_RUNNING -eq 1 ]; then
            log_success "All services operational."
        fi

        exit 0
    fi

    if [ $UP -eq 1 ]; then
        log_info "Starting MongoDB, QdrantDB, ZenML, PostgreSQL, and MLFlow services..."
        docker compose --env-file "$ENV_FILE" -f "$DOCKER_COMPOSE_FILE" up -d
        log_success "Services successfully started!"
        sleep "$SERVICE_STARTUP_DELAY"
        log_info "Connecting to ZenML server..."
        uvx zenml login "$ZENML_SERVER_URL"
        log_success "Successfully connected to ZenML server."
        log_info "Integrating MLFlow with ZenML..."
        uvx zenml integration install mlflow --uv --yes
        if ! uvx zenml experiment-tracker list | grep -q "mlflow_docker"; then
            uvx zenml experiment-tracker register mlflow_docker --flavor=mlflow \
                --tracking_uri="$MLFLOW_SERVER_URL" \
                --tracking_username="{{settings.MLFLOW_USERNAME}}" \
                --tracking_password="{{settings.MLFLOW_PASSWORD}}"
        fi
        if ! uvx zenml stack list | grep -q "mlflow_stack"; then
            uvx zenml stack copy default mlflow_stack
            uvx zenml stack update mlflow_stack -e mlflow_docker
            uvx zenml stack set mlflow_stack
        fi
        log_success "MLFlow successfully integrated within ZenML..."
        exit 0
    fi

    if [ $DOWN -eq 1 ]; then
        log_info "Disconnecting from ZenML server..."
        uvx zenml logout "$ZENML_SERVER_URL" --clear
        log_success "Successfully disconnected from ZenML server."
        log_info "Stopping MongoDB, QdrantDB, ZenML, PostgreSQL, and MLFlow services..."
        docker compose --env-file "$ENV_FILE" -f "$DOCKER_COMPOSE_FILE" stop
        log_success "Services successfully stopped!"
        exit 0
    fi
}

# Manage settings
manage_settings() {
    EXPORT=0
    DROP=0

    while [ $# -gt 0 ]; do
        case "$1" in
            --export) EXPORT=1 ;;
            --drop) DROP=1 ;;
            *)
                log_error "Unknown option for 'settings': $1"
                echo ""
                echo "Usage: $(basename "$0") settings [--export|--drop]"
                exit 1
                ;;
        esac
        shift
    done

    if [ "$EXPORT" = 1 ] && [ "$DROP" = 1 ]; then
        log_error "Options --export and --drop are mutually exclusive."
        exit 1
    elif [ "$EXPORT" = 0 ] && [ "$DROP" = 0 ]; then
        log_error "You must specify either --export or --drop."
        exit 1
    fi

    SETTINGS_PATH="$SCRIPT_DIR/src/shared/adapters/cli/manage_settings.py"
    if [ "$EXPORT" = 1 ]; then
        uv run "$SETTINGS_PATH" --export
        exit 0
    fi

    if [ "$DROP" = 1 ]; then
        uv run "$SETTINGS_PATH" --drop
        exit 0
    fi
}

# Manage pipelines
manage_pipeline() {
    NO_CACHE=0
    CONFIG_FILE=""
    RUN_ETL=0
    RUN_RAG=0
    RUN_ALL=0

    while [ $# -gt 0 ]; do
        case "$1" in
            --no-cache) NO_CACHE=1 ;;
            --etl) RUN_ETL=1 ;;
            --rag) RUN_RAG=1 ;;
            --all) RUN_ALL=1 ;;
            --config|-c)
                shift
                if [ $# -eq 0 ]; then
                    log_error "Missing argument for $1"
                    echo ""
                    echo "Usage: $(basename "$0") pipeline [--no-cache] --etl|--rag|--all --config FILE"
                    exit 1
                fi
                CONFIG_FILE="$1"
                ;;
            *)
                log_error "Unknown option for 'pipeline': $1"
                echo ""
                echo "Usage: $(basename "$0") pipeline [--no-cache] --etl|--rag|--all --config FILE"
                exit 1
                ;;
        esac
        shift
    done

    if [ -z "$CONFIG_FILE" ]; then
        log_error "The --config argument is required."
        echo ""
        echo "Usage: $(basename "$0") pipeline [--no-cache] --etl|--rag|--all --config FILE"
        exit 1
    fi

    if [ $RUN_ETL -eq 0 ] && [ $RUN_RAG -eq 0 ] && [ $RUN_ALL -eq 0 ]; then
        log_error "One of options --etl, --rag, or --all is required."
        echo ""
        echo "Usage: $(basename "$0") pipeline [--no-cache] --etl|--rag|--all --config FILE"
        exit 1
    fi

    if [ $RUN_ETL -eq 1 ] && [ $RUN_ALL -eq 1 ]; then
        log_warning "Options --all with --etl is redundant."
    fi

    if [ $RUN_RAG -eq 1 ] && [ $RUN_ALL -eq 1 ]; then
        log_warning "Options --all with --rag is redundant."
    fi

    if [ $RUN_ETL -eq 1 ] || [ $RUN_ALL -eq 1 ]; then
        ETL_PATH="$SCRIPT_DIR/src/etl/adapters/cli/run_pipelines.py"
        if [ $NO_CACHE -eq 1 ]; then
            uv run "$ETL_PATH" --no-cache --config "$CONFIG_FILE"
        else
            uv run "$ETL_PATH" --config "$CONFIG_FILE"
        fi
    fi

    if [ $RUN_RAG -eq 1 ] || [ $RUN_ALL -eq 1 ]; then
        RAG_PATH="$SCRIPT_DIR/src/rag/adapters/cli/run_pipelines.py"
        if [ $NO_CACHE -eq 1 ]; then
            uv run "$RAG_PATH" --no-cache --config "$CONFIG_FILE"
        else
            uv run "$RAG_PATH" --config "$CONFIG_FILE"
        fi
    fi

    exit 0
}

# Top-level argument parsing
if [ $# -eq 0 ]; then
    usage
    exit 1
fi

COMMAND="$1"
shift

case "$COMMAND" in
    -h|--help)
        usage
        exit 0
        ;;
    -v|--version)
        echo "$VERSION"
        exit 0
        ;;
    infra)
        manage_infra "$@"
        ;;
    settings)
        manage_settings "$@"
        ;;
    pipeline)
        manage_pipeline "$@"
        ;;
    *)
        log_error "Unknown command: $COMMAND"
        echo ""
        usage
        exit 1
        ;;
esac
