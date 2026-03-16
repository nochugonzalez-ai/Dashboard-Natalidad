# 1. Definimos el proveedor (GCP en este caso)
provider "google" {
  project = "dashboard-476401" # El ID de BigQuery
  region  = "us-central1"
  credentials = file("D:\\Udemy\\Portafolio\\Tablero\\dashboard.json:/app/gcp-key.json")
}

# 2. Creamos una Red Virtual (VPC)
resource "google_compute_network" "vpc_network" {
  name = "dashboard-network"
}

# 3. Creamos una instancia de Servidor (VM) donde correrá Docker
resource "google_compute_instance" "vm_instance" {
  name         = "dashboard-server"
  machine_type = "f1-micro" # La más barata/gratis
  zone         = "us-central1-a"

  boot_disk {
    initialize_params {
      image = "debian-cloud/debian-11"
    }
  }

  network_interface {
    network = google_compute_network.vpc_network.name
    access_config {
      # Esto le da una IP pública para ver Grafana
    }
  }

  # Script de inicio: Instala Docker automáticamente al encenderse
  metadata_startup_script = <<-EOT
    sudo apt-get update
    sudo apt-get install -y docker.io docker-compose
    git clone https://github.com/tu-usuario/tu-repositorio.git
    cd tu-repositorio
    docker-compose up -d
  EOT
}

# 4. Regla de Firewall para abrir el puerto de Grafana (3000)
resource "google_compute_firewall" "default" {
  name    = "allow-grafana"
  network = google_compute_network.vpc_network.name

  allow {
    protocol = "tcp"
    ports    = ["3000"]
  }

  source_ranges = ["0.0.0.0/0"] # Permite acceso desde cualquier IP
}