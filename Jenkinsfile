// CI/CD for the 3-tier app: build both images, push to GHCR, deploy to the
// App EC2 over SSH, then verify. Stage-by-stage rationale lives in
// deployment-docs/09-ci-cd-pipeline-flow.md — keep the two in sync.
pipeline {
    agent any

    environment {
        REGISTRY        = 'ghcr.io'
        OWNER           = 'OWNER'                // TODO: your GitHub username/org (lowercase)
        BACKEND_IMAGE   = "${REGISTRY}/${OWNER}/devops-fullstack-project1-backend"
        FRONTEND_IMAGE  = "${REGISTRY}/${OWNER}/devops-fullstack-project1-frontend"
        APP_EC2_HOST    = 'deployer@APP_EC2_PRIVATE_IP'  // TODO: real private IP
        APP_DIR         = '/opt/app'
        IMAGE_TAG       = "${env.GIT_COMMIT.take(7)}"
    }

    options {
        timestamps()
        disableConcurrentBuilds()
    }

    stages {
        stage('Build images') {
            steps {
                sh """
                    docker build -t ${BACKEND_IMAGE}:${IMAGE_TAG} -t ${BACKEND_IMAGE}:latest ./backend
                    docker build -t ${FRONTEND_IMAGE}:${IMAGE_TAG} -t ${FRONTEND_IMAGE}:latest ./frontend
                """
            }
        }

        stage('Push to GHCR') {
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'ghcr-credentials',
                    usernameVariable: 'GHCR_USER',
                    passwordVariable: 'GHCR_TOKEN'
                )]) {
                    sh """
                        echo "\$GHCR_TOKEN" | docker login ${REGISTRY} -u "\$GHCR_USER" --password-stdin
                        docker push ${BACKEND_IMAGE}:${IMAGE_TAG}
                        docker push ${BACKEND_IMAGE}:latest
                        docker push ${FRONTEND_IMAGE}:${IMAGE_TAG}
                        docker push ${FRONTEND_IMAGE}:latest
                    """
                }
            }
        }

        stage('Deploy to App EC2') {
            steps {
                sshagent(credentials: ['app-ec2-ssh-key']) {
                    sh """
                        ssh -o StrictHostKeyChecking=no ${APP_EC2_HOST} '
                            cd ${APP_DIR} &&
                            sed -i "s#^BACKEND_IMAGE=.*#BACKEND_IMAGE=${BACKEND_IMAGE}:${IMAGE_TAG}#" .env &&
                            sed -i "s#^FRONTEND_IMAGE=.*#FRONTEND_IMAGE=${FRONTEND_IMAGE}:${IMAGE_TAG}#" .env &&
                            docker compose pull &&
                            docker compose up -d
                        '
                    """
                }
            }
        }

        stage('Verify') {
            steps {
                sshagent(credentials: ['app-ec2-ssh-key']) {
                    sh """
                        ssh -o StrictHostKeyChecking=no ${APP_EC2_HOST} 'curl -fsS http://localhost/healthz'
                    """
                }
            }
        }
    }

    post {
        failure {
            echo "Build ${IMAGE_TAG} failed — previous containers on the App EC2 were left running untouched."
        }
        always {
            sh "docker logout ${REGISTRY} || true"
        }
    }
}
