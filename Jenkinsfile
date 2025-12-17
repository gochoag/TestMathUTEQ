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
                    bat 'copy "%ENV_FILE%" .env'
                }
            }
        }

        stage('Desplegar') {
            steps {
                bat 'docker compose down --remove-orphans || exit 0'
                bat 'docker compose up -d --build'
            }
        }
    }
}
