data "template_file" "setup_langflow" {
  template = file("setup_langflow.tpl.sh")
  vars = {
    certbot_email               = var.certbot_email
    langflow_superuser          = var.langflow_superuser
    langflow_superuser_password = var.langflow_superuser_password
    langflow_secret_key         = var.langflow_secret_key
    postgres_url                = var.postgres_url
    openai_api_key              = var.openai_api_key
    langflow_domain             = var.langflow_domain
    aws_region                  = var.aws_region
    aws_account_id              = var.aws_account_id
    image_tag                   = var.image_tag
  }
}

resource "aws_lightsail_instance" "langflow_virtual_server_new" {
  name              = "langflow-instance-new"
  availability_zone = var.aws_availability_zone
  blueprint_id      = var.instance_blueprint_id
  bundle_id         = var.instance_bundle_id
  key_pair_name     = var.lightsail_key_pair
  user_data         = data.template_file.setup_langflow.rendered

  tags = {
    Environment = "Production"
    Application = "Langflow"
  }
}

resource "aws_lightsail_instance_public_ports" "langflow_virtual_server_new_ports" {
  instance_name = aws_lightsail_instance.langflow_virtual_server_new.name

  port_info {
    from_port = 22
    to_port   = 22
    protocol  = "tcp"
  }

  port_info {
    from_port = 80
    to_port   = 80
    protocol  = "tcp"
  }

  port_info {
    from_port = 443
    to_port   = 443
    protocol  = "tcp"
  }
}


