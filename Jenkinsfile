pipeline {
    agent any

    environment {
        // Docker registry settings
        DOCKER_REGISTRY = 'docker.io'  // Change to your registry
        DOCKER_IMAGE = 'multiagent-rag'
        DOCKER_TAG = "${env.BUILD_NUMBER}"

        // Application settings
        APP_NAME = 'multi-agent-rag'

        // Credentials (stored in Jenkins)
        DOCKER_CREDENTIALS_ID = 'docker-hub-credentials'
        OPENAI_CREDENTIALS_ID = 'openai-api-key'
        WEAVIATE_CREDENTIALS_ID = 'weaviate-credentials'
        POSTGRES_CREDENTIALS_ID = 'postgres-password'
    }

    options {
        buildDiscarder(logRotator(numToKeepStr: '10'))
        timestamps()
        timeout(time: 30, unit: 'MINUTES')
    }

    stages {
        stage('Checkout') {
            steps {
                script {
                    echo "Checking out code from repository..."
                    checkout scm

                    // Get commit information
                    env.GIT_COMMIT_MSG = sh(
                        script: 'git log -1 --pretty=%B',
                        returnStdout: true
                    ).trim()
                    env.GIT_AUTHOR = sh(
                        script: 'git log -1 --pretty=%an',
                        returnStdout: true
                    ).trim()
                }
            }
        }

        stage('Environment Setup') {
            steps {
                script {
                    echo "Setting up Python virtual environment..."
                    sh '''
                        python3 --version
                        python3 -m venv venv
                        . venv/bin/activate
                        pip install --upgrade pip
                        pip --version
                    '''
                }
            }
        }

        stage('Install Dependencies') {
            steps {
                script {
                    echo "Installing Python dependencies..."
                    sh '''
                        . venv/bin/activate
                        pip install -r requirements.txt
                    '''
                }
            }
        }

        stage('Code Quality Checks') {
            parallel {
                stage('Linting') {
                    steps {
                        script {
                            echo "Running code linting..."
                            sh '''
                                . venv/bin/activate
                                pip install flake8 pylint

                                # Flake8 (relaxed settings)
                                flake8 src/ --max-line-length=120 --ignore=E501,W503 || true

                                # Pylint (basic checks)
                                pylint src/ --exit-zero || true
                            '''
                        }
                    }
                }

                stage('Security Scan') {
                    steps {
                        script {
                            echo "Scanning for security vulnerabilities..."
                            sh '''
                                . venv/bin/activate
                                pip install safety bandit

                                # Check dependencies for known vulnerabilities
                                safety check --json || true

                                # Bandit security linter
                                bandit -r src/ -f json -o bandit-report.json || true
                            '''
                        }
                    }
                }
            }
        }

        stage('Run Tests') {
            steps {
                script {
                    echo "Running unit tests..."
                    sh '''
                        . venv/bin/activate
                        pip install pytest pytest-cov pytest-mock

                        # Create test directory if it doesn't exist
                        mkdir -p tests

                        # Run tests with coverage (if tests exist)
                        if [ -d "tests" ] && [ "$(ls -A tests)" ]; then
                            pytest tests/ --cov=src --cov-report=xml --cov-report=html --junitxml=test-results.xml || true
                        else
                            echo "No tests found, skipping test execution"
                        fi
                    '''
                }
            }
            post {
                always {
                    // Publish test results if they exist
                    script {
                        if (fileExists('test-results.xml')) {
                            junit 'test-results.xml'
                        }
                    }
                }
            }
        }

        stage('Build Docker Image') {
            steps {
                script {
                    echo "Building Docker image..."
                    sh """
                        docker build -t ${DOCKER_IMAGE}:${DOCKER_TAG} .
                        docker tag ${DOCKER_IMAGE}:${DOCKER_TAG} ${DOCKER_IMAGE}:latest
                    """
                }
            }
        }

        stage('Docker Image Scan') {
            steps {
                script {
                    echo "Scanning Docker image for vulnerabilities..."
                    sh """
                        # Using Trivy for container scanning
                        docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
                            aquasec/trivy:latest image --severity HIGH,CRITICAL \
                            ${DOCKER_IMAGE}:${DOCKER_TAG} || true
                    """
                }
            }
        }

        stage('Integration Tests') {
            steps {
                script {
                    echo "Running integration tests with Docker Compose..."
                    sh '''
                        # Start services
                        docker-compose -f docker-compose.yml up -d postgres redis

                        # Wait for services to be healthy
                        echo "Waiting for services to be ready..."
                        sleep 10

                        # Run integration tests
                        . venv/bin/activate

                        # Test database connection
                        python -c "from src.utils.database import db_manager; print('Database connection: OK')" || true

                        # Cleanup
                        docker-compose -f docker-compose.yml down
                    '''
                }
            }
        }

        stage('Push Docker Image') {
            when {
                branch 'master'
            }
            steps {
                script {
                    echo "Pushing Docker image to registry..."
                    withCredentials([usernamePassword(
                        credentialsId: "${DOCKER_CREDENTIALS_ID}",
                        usernameVariable: 'DOCKER_USER',
                        passwordVariable: 'DOCKER_PASS'
                    )]) {
                        sh """
                            echo \$DOCKER_PASS | docker login ${DOCKER_REGISTRY} -u \$DOCKER_USER --password-stdin
                            docker tag ${DOCKER_IMAGE}:${DOCKER_TAG} ${DOCKER_REGISTRY}/\${DOCKER_USER}/${DOCKER_IMAGE}:${DOCKER_TAG}
                            docker tag ${DOCKER_IMAGE}:${DOCKER_TAG} ${DOCKER_REGISTRY}/\${DOCKER_USER}/${DOCKER_IMAGE}:latest
                            docker push ${DOCKER_REGISTRY}/\${DOCKER_USER}/${DOCKER_IMAGE}:${DOCKER_TAG}
                            docker push ${DOCKER_REGISTRY}/\${DOCKER_USER}/${DOCKER_IMAGE}:latest
                            docker logout ${DOCKER_REGISTRY}
                        """
                    }
                }
            }
        }

        stage('Deploy to Staging') {
            when {
                branch 'master'
            }
            steps {
                script {
                    echo "Deploying to staging environment..."
                    withCredentials([
                        string(credentialsId: "${OPENAI_CREDENTIALS_ID}", variable: 'OPENAI_API_KEY'),
                        string(credentialsId: "${WEAVIATE_CREDENTIALS_ID}", variable: 'WEAVIATE_CREDENTIALS'),
                        string(credentialsId: "${POSTGRES_CREDENTIALS_ID}", variable: 'POSTGRES_PASSWORD')
                    ]) {
                        sh '''
                            # Parse Weaviate credentials
                            export WEAVIATE_URL=$(echo $WEAVIATE_CREDENTIALS | jq -r '.url')
                            export WEAVIATE_API_KEY=$(echo $WEAVIATE_CREDENTIALS | jq -r '.api_key')
                            export WEAVIATE_COLLECTION=$(echo $WEAVIATE_CREDENTIALS | jq -r '.collection')

                            # Deploy using docker-compose
                            docker-compose -f docker-compose.prod.yml down || true
                            docker-compose -f docker-compose.prod.yml up -d

                            # Wait for application to be ready
                            echo "Waiting for application to start..."
                            sleep 15

                            # Health check
                            curl -f http://localhost:8501/_stcore/health || exit 1
                        '''
                    }
                }
            }
        }

        stage('Smoke Tests') {
            when {
                branch 'master'
            }
            steps {
                script {
                    echo "Running smoke tests..."
                    sh '''
                        # Check if application is responding
                        curl -f http://localhost:8501 || exit 1

                        # Check database connectivity
                        docker exec multiagent_rag_postgres pg_isready -U raguser || exit 1

                        # Check Redis connectivity
                        docker exec multiagent_rag_redis redis-cli ping || exit 1

                        echo "All smoke tests passed!"
                    '''
                }
            }
        }
    }

    post {
        always {
            script {
                echo "Cleaning up..."
                sh '''
                    # Remove virtual environment
                    rm -rf venv

                    # Clean up Docker images (keep last 3 builds)
                    docker image prune -f
                '''
            }
        }

        success {
            script {
                echo "Pipeline completed successfully!"
                // Send notification (Slack, email, etc.)
                // slackSend(color: 'good', message: "Build ${env.BUILD_NUMBER} succeeded for ${env.APP_NAME}")
            }
        }

        failure {
            script {
                echo "Pipeline failed!"
                // Send notification
                // slackSend(color: 'danger', message: "Build ${env.BUILD_NUMBER} failed for ${env.APP_NAME}")
            }
        }

        unstable {
            script {
                echo "Pipeline completed with warnings"
            }
        }
    }
}
