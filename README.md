![image](https://img.shields.io/badge/Bulma-00D1B2?style=for-the-badge&logo=Bulma&logoColor=white) ![image](https://img.shields.io/badge/Docker-2CA5E0?style=for-the-badge&logo=docker&logoColor=white)  ![image](https://img.shields.io/badge/Python-FFD43B?style=for-the-badge&logo=python&logoColor=blue)
# minecraft-server-spawner
Deploy any version of minecraft and forge as a container at a mass scale.

This project is made with Python for the backend, [Bottle](https://bottlepy.org/docs/dev/) and [Bulma CSS](https://bulma.io/) for the frontend. Uses [itzg's docker image](https://hub.docker.com/r/itzg/minecraft-server) through Docker to spawn instances of minecraft or forge based on the parameters provided from the web interface. Web interface gives you an easy way to manage, configure and update the server instances.

The point of this project was to keep everything as light and simple as possible while utilizing python.

## Features

- Deploy multiple Minecraft server instances with ease.
- Supports both vanilla Minecraft and Forge modded servers.
- Manage server instances through a simple web interface.
- Start, stop, and monitor server instances.
- Add or remove mods dynamically.
- View server logs and status.

## Installation

1. Clone the repository:
    ```sh
    git clone <repository-url>
    cd minecraft-server-spawner
    ```

2. Create and activate a virtual environment:
    ```sh
    python3 -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3. Install the required dependencies:
    ```sh
    pip install -r requirements.txt
    ```

4. Copy the example environment file and configure it:
    ```sh
    cp .env.example .env
    # Edit .env to match your configuration
    ```

## Usage

1. Start the application:
    ```sh
    python app.py
    ```

2. Access the web interface at `http://localhost:8000`.

3. Use the web interface to manage your Minecraft server instances.

## License

This project is licensed under the GNU General Public License v3.0. See the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request. \
Refer to the TODO section for ideas on how to contribute.

## TODO

- Admin/authentication interface to give people an account and a limit of how many servers they can spawn (through some kind of token system)
- Bukkit/Spigot support
- Fabric support
- Magma/Ketting/Mohist support
- Adding more parameters such as min and max of RAM and different versions of Java
- Nice UI for server properties that synch through the docker-compose instead of read/write the server.properties file
- Support for changing configuration files for mods
- Actual error handling
- Cluster/Server information on the home page
- Create dockerfile for project

## Contact

For any inquiries, please contact the author at `ftechhelp@gmail.com`.

## Acknowledgements

- [Bottle](https://bottlepy.org/docs/dev/) - A fast, simple and lightweight WSGI micro web-framework for Python.
- [Bulma CSS](https://bulma.io/) - A modern CSS framework based on Flexbox.
- [itzg's docker image](https://hub.docker.com/r/itzg/minecraft-server) - Docker image for running Minecraft servers.
- [python-on-whales](https://gabrieldemarmiesse.github.io/python-on-whales/) - A Python library for Docker.
