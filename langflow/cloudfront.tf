# Origin-only A record -> your Lightsail instance
resource "aws_route53_record" "langflow_origin" {
  zone_id = data.aws_route53_zone.primary.zone_id
  name    = "origin-langflow.dodao.io"
  type    = "A"
  ttl     = 300
  records = [aws_lightsail_instance.langflow_docker_instance.public_ip_address]
}

# CloudFront distribution in front of the origin
resource "aws_cloudfront_distribution" "langflow" {
  enabled         = true
  is_ipv6_enabled = true
  comment         = "Langflow via CloudFront"
  aliases         = ["langflow.dodao.io"]
  price_class     = "PriceClass_100"

  # --- origin (singular)
  origin {
    origin_id   = "lightsail-origin"
    domain_name = "origin-langflow.dodao.io"

    # Only HTTP to the Lightsail Nginx
    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "http-only"
      origin_ssl_protocols   = ["TLSv1.2"]
    }

    # (optional) Shared secret header so origin only serves via CloudFront
    dynamic "custom_header" {
      for_each = var.cf_origin_secret != "" ? [1] : []
      content {
        name  = "X-CF-Secret"
        value = var.cf_origin_secret
      }
    }
  }

  # --- default behavior (must include allowed_methods & cached_methods)
  default_cache_behavior {
    target_origin_id       = "lightsail-origin"
    viewer_protocol_policy = "redirect-to-https"
    compress               = true

    # All methods allowed; only GET/HEAD cached
    allowed_methods = ["GET","HEAD","OPTIONS","PUT","POST","PATCH","DELETE"]
    cached_methods  = ["GET","HEAD"]

    # Managed policies:
    #   - CachingDisabled (no caching)
    #   - AllViewer (forward all headers/cookies/query to origin)
    cache_policy_id          = "4135ea2d-6df8-44a3-9df3-4b5a84be39ad"
    origin_request_policy_id = "216adef6-5c7f-47e4-b989-5492eafa07d3"
  }

  # --- required block
  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  # ACM cert (validated in us-east-1)
  viewer_certificate {
    acm_certificate_arn      = aws_acm_certificate_validation.cf_cert.certificate_arn
    ssl_support_method       = "sni-only"
    minimum_protocol_version = "TLSv1.2_2021"
  }

  depends_on = [aws_acm_certificate_validation.cf_cert]
}

# Replace your old langflow.dodao.io A record with ALIAS to CloudFront
resource "aws_route53_record" "langflow_dns_via_cf" {
  zone_id = data.aws_route53_zone.primary.zone_id
  name    = "langflow.dodao.io"
  type    = "A"
  alias {
    name                   = aws_cloudfront_distribution.langflow.domain_name
    zone_id                = aws_cloudfront_distribution.langflow.hosted_zone_id
    evaluate_target_health = false
  }
}
