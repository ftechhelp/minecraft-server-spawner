#!/bin/bash

# Initialize variables
MINECRAFT_VERSION=""
FORGE_VERSION=""
PORT=""

# Function to print help message
print_help() {
    echo "Usage: $0 [OPTIONS]"
    echo "Options:"
    echo "  --minecraftVersion VERSION   Specify Minecraft version"
    echo "  --forgeVersion VERSION       Specify Forge version"
    echo "  --port NUMBER                Specify port number"
    echo "  --name STRING                Specify the name of the container"
    echo "  --help                       Show this help message"
    echo ""
    echo "Example:"
    echo "  $0 --forgeVersion 40.2.0 --minecraftVersion 1.18.2 --port 5000"
}

# Parse command line arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --minecraftVersion) MINECRAFT_VERSION="$2"; shift ;;
        --forgeVersion) FORGE_VERSION="$2"; shift ;;
        --port) PORT="$2"; shift ;;
        --name) NAME="$2"; shift ;;
        --help) print_help; exit 0 ;;
        *) echo "Unknown parameter: $1"; print_help; exit 1 ;;
    esac
    shift
done

# Check if required parameters are provided
if [ -z "$MINECRAFT_VERSION" ] || [ -z "$FORGE_VERSION" ] || [ -z "$PORT" ] || [ -z "$NAME" ]; then
    echo "Error: Missing required parameters."
    print_help
    exit 1
fi

# Build Docker image
echo "Building Forge container with the following parameters:"
echo "Minecraft Version: $MINECRAFT_VERSION"
echo "Forge Version: $FORGE_VERSION"
echo "Name: $NAME"
echo "Port: $PORT"

# Run the container
docker run \
    -d -it -p $PORT:25565 \
    -e EULA=TRUE \
    -e TYPE=FORGE \
    -e VERSION=$MINECRAFT_VERSION \
    -e FORGE_VERSION=$FORGE_VERSION \
    --name forge-server-$PORT-$MINECRAFT_VERSION-$FORGE_VERSION-$NAME \
    itzg/minecraft-server

echo "Forge container built and launched successfully."