pipeline {
    agent any

    environment {
        DOCKER_API_VERSION = '1.41'
    }

    stages {
        stage('Configurar') {
            steps {
                checkout scm
                withCredentials([file(credentialsId: 'testmath-uteq', variable: 'ENV_FILE')]) {
                    sh 'cp "$ENV_FILE" .env'
                }
            }
        }

        stage('Desplegar') {
            steps {
                sh 'docker compose down --remove-orphans || true'
                sh 'docker compose up -d --build'
            }
        }

        stage('Verificar') {
            steps {
                sh 'sleep 5'
                sh 'docker ps -a | grep testmath'
                sh 'docker exec webtestmathuteq ls -la /app || true'
                sh 'docker exec webtestmathuteq ls -la /app/matholymp || true'
                sh 'docker logs webtestmathuteq --tail 20 || true'
            }
        }
    }
}
