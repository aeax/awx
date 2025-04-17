variable "librenms_url" {
  description = "URL of the LibreNMS server"
  type = string
}

variable "librenms_api_token" {
  description = "API token for LibreNMS"
  type = string
  sensitive = true
} 