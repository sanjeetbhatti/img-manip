## Image Manipulation 
## Quick Start

1. Clone the repository
2. Run `docker-compose up -d`
3. Access the app at `http://localhost:8000`

#### Feature/idea List

- [X] containerize app (with docker)
- [X] multi format support (png, jpeg, etc)
- [X] frontend
- [X] add database to store previous results
- [X] concurrent user support (async/await with ThreadPoolExecutor)
- [ ] loading bar/circle
- [ ] display file stats
- [ ] multiprocessing (speed up)
- [ ] size limit on uploaded files
- [ ] delete compressed files after 1 hour (on this server)
- [ ] cached result (maybe append the parameter value to the filename)
- [ ] single source file (works as cached file) and allow user to run permutation of settings

### Access Points
- **Main App**: http://localhost:8000
- **Database Admin**: http://localhost:8080 (Adminer)

## Technical Implementation

- **Backend**: FastAPI with async/await patterns
- **Database**: MySQL with ThreadPoolExecutor for async operations
- **Image Processing**: Pillow (PIL) for compression
- **Containerization**: Docker Compose with health checks
- **Frontend**: HTML/CSS/JavaScript with Jinja2 templating

## Performance Features

- **Concurrent User Support**: ThreadPoolExecutor prevents event loop blocking
- **Database Persistence**: Previous uploads stored and retrievable
- **Health Checks**: Docker Compose ensures reliable startup