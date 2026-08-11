"""
Utilidades para el envío de correos electrónicos
"""

import datetime
from html import escape

from django.conf import settings


def generate_participants_list_email(
    *, nombre, grupo_nombre, concurso_nombre, carrera_nombre, participantes
):
    """Genera el correo institucional con las credenciales de un grupo.

    Usa tablas y estilos inline para conservar la estructura en Gmail, Outlook
    y clientes móviles, donde el CSS avanzado y las fuentes externas no son
    confiables.
    """
    current_year = datetime.datetime.now().year
    site_url = getattr(settings, 'SITE_URL', 'http://localhost:8000').rstrip('/')
    login_url = f"{site_url}/login/"
    support_email = getattr(
        settings, 'SUPPORT_EMAIL', 'olimpiadasmecanicauteq@gmail.com'
    )

    recipient_name = escape(str(nombre))
    group_name = escape(str(grupo_nombre))
    contest_name = escape(str(concurso_nombre))
    program_name = escape(str(carrera_nombre))
    safe_support_email = escape(str(support_email))

    rows = []
    for index, participante in enumerate(participantes, start=1):
        row_background = '#f8fbf9' if index % 2 == 0 else '#ffffff'
        rows.append(
            f"""
            <tr>
                <td style="padding:12px 8px;border-bottom:1px solid #e7ece9;color:#68736e;font-size:12px;text-align:center;background:{row_background};">{index}</td>
                <td style="padding:12px 10px;border-bottom:1px solid #e7ece9;color:#1e2b25;font-size:13px;font-weight:700;line-height:18px;background:{row_background};">{escape(str(participante['nombre']))}</td>
                <td style="padding:12px 8px;border-bottom:1px solid #e7ece9;color:#35423b;font-size:12px;background:{row_background};">{escape(str(participante['cedula']))}</td>
                <td style="padding:12px 8px;border-bottom:1px solid #e7ece9;color:#28724c;font-size:12px;word-break:break-word;background:{row_background};">{escape(str(participante['email']))}</td>
                <td style="padding:12px 8px;border-bottom:1px solid #e7ece9;color:#1e2b25;font-family:Consolas,'Courier New',monospace;font-size:12px;background:{row_background};">{escape(str(participante['username']))}</td>
                <td style="padding:12px 8px;border-bottom:1px solid #e7ece9;color:#79550a;font-family:Consolas,'Courier New',monospace;font-size:12px;font-weight:700;background:#fff8e8;">{escape(str(participante['password']))}</td>
            </tr>
            """
        )

    participants_rows = ''.join(rows)
    total_participantes = len(participantes)
    plain_lines = '\n'.join(
        f"{index}. {participant['nombre']} | Cédula: {participant['cedula']} | "
        f"Usuario: {participant['username']} | Contraseña: {participant['password']}"
        for index, participant in enumerate(participantes, start=1)
    )
    plain_message = f"""Estimado/a {nombre},

Se generó la lista de participantes asignados al grupo "{grupo_nombre}".

Concurso: {concurso_nombre}
Carrera: {carrera_nombre}
Total de participantes: {total_participantes}

Las credenciales incluidas son confidenciales. Compártalas únicamente con cada
participante y evite reenviar este correo.

{plain_lines}

Acceso a la plataforma: {login_url}
Soporte: {support_email}

Atentamente,
{carrera_nombre}
Universidad Técnica Estatal de Quevedo
"""

    html_message = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Participantes asignados</title>
</head>
<body style="margin:0;padding:0;background-color:#f2f5f3;font-family:Arial,Helvetica,sans-serif;color:#1e2b25;">
  <div style="display:none;max-height:0;overflow:hidden;opacity:0;color:transparent;">
    Lista y credenciales de {total_participantes} participantes del grupo {group_name}.
  </div>
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="width:100%;background-color:#f2f5f3;">
    <tr>
      <td align="center" style="padding:28px 12px;">
        <table role="presentation" width="720" cellspacing="0" cellpadding="0" border="0" style="width:100%;max-width:720px;background-color:#ffffff;border:1px solid #dce5df;">
          <tr>
            <td style="padding:32px 34px 28px;background-color:#087c3f;border-bottom:5px solid #f0a429;">
              <p style="margin:0 0 8px;color:#d7f0e0;font-size:12px;font-weight:700;letter-spacing:1.1px;text-transform:uppercase;">EVAUTEQ · Gestión de participantes</p>
              <h1 style="margin:0;color:#ffffff;font-size:27px;line-height:34px;font-weight:700;">Participantes asignados</h1>
              <p style="margin:10px 0 0;color:#e6f5eb;font-size:15px;line-height:22px;">Información para el representante del grupo</p>
            </td>
          </tr>
          <tr>
            <td style="padding:32px 34px 18px;">
              <p style="margin:0 0 16px;font-size:16px;line-height:24px;">Estimado/a <strong>{recipient_name}</strong>,</p>
              <p style="margin:0;font-size:15px;line-height:24px;color:#435149;">A continuación encontrará la relación de estudiantes asignados y sus credenciales de acceso. Comparta cada credencial únicamente con su respectivo participante.</p>
            </td>
          </tr>
          <tr>
            <td style="padding:0 34px 22px;">
              <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="width:100%;background-color:#f4f8f5;border:1px solid #dce8e0;">
                <tr>
                  <td style="padding:16px 18px;border-left:4px solid #087c3f;">
                    <p style="margin:0 0 5px;color:#66736c;font-size:11px;font-weight:700;letter-spacing:0.8px;text-transform:uppercase;">Grupo</p>
                    <p style="margin:0;color:#173c27;font-size:17px;font-weight:700;">{group_name}</p>
                    <p style="margin:8px 0 0;color:#526058;font-size:13px;line-height:19px;">{contest_name} · {program_name}</p>
                  </td>
                  <td align="center" width="116" style="padding:16px 12px;border-left:1px solid #dce8e0;">
                    <p style="margin:0;color:#087c3f;font-size:28px;line-height:30px;font-weight:700;">{total_participantes}</p>
                    <p style="margin:5px 0 0;color:#66736c;font-size:11px;font-weight:700;text-transform:uppercase;">Participantes</p>
                  </td>
                </tr>
              </table>
            </td>
          </tr>
          <tr>
            <td style="padding:0 34px 24px;">
              <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="width:100%;background-color:#fff8e8;border:1px solid #f4deb0;">
                <tr>
                  <td style="padding:15px 17px;border-left:4px solid #d68c00;">
                    <p style="margin:0 0 4px;color:#765000;font-size:14px;font-weight:700;">Información confidencial</p>
                    <p style="margin:0;color:#705a27;font-size:13px;line-height:19px;">Las contraseñas de esta lista se generaron con este envío. No reenvíe el correo completo ni publique las credenciales en grupos o redes sociales.</p>
                  </td>
                </tr>
              </table>
            </td>
          </tr>
          <tr>
            <td style="padding:0 34px 12px;">
              <h2 style="margin:0;color:#173c27;font-size:18px;line-height:26px;">Listado de acceso</h2>
              <p style="margin:5px 0 0;color:#66736c;font-size:13px;line-height:19px;">Usuario y contraseña temporal para el acceso inicial a la plataforma.</p>
            </td>
          </tr>
          <tr>
            <td style="padding:0 22px 22px;">
              <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="width:100%;border:1px solid #dce5df;border-collapse:collapse;">
                <thead>
                  <tr>
                    <th align="center" style="padding:12px 6px;background-color:#145a35;color:#ffffff;font-size:11px;line-height:15px;">#</th>
                    <th align="left" style="padding:12px 8px;background-color:#145a35;color:#ffffff;font-size:11px;line-height:15px;">PARTICIPANTE</th>
                    <th align="left" style="padding:12px 6px;background-color:#145a35;color:#ffffff;font-size:11px;line-height:15px;">CÉDULA</th>
                    <th align="left" style="padding:12px 6px;background-color:#145a35;color:#ffffff;font-size:11px;line-height:15px;">CORREO</th>
                    <th align="left" style="padding:12px 6px;background-color:#145a35;color:#ffffff;font-size:11px;line-height:15px;">USUARIO</th>
                    <th align="left" style="padding:12px 6px;background-color:#145a35;color:#ffffff;font-size:11px;line-height:15px;">CONTRASEÑA</th>
                  </tr>
                </thead>
                <tbody>{participants_rows}</tbody>
              </table>
            </td>
          </tr>
          <tr>
            <td align="center" style="padding:2px 34px 32px;">
              <a href="{login_url}" style="display:inline-block;padding:13px 22px;background-color:#087c3f;color:#ffffff;font-size:14px;font-weight:700;text-decoration:none;border-radius:4px;">Abrir plataforma EVAUTEQ</a>
            </td>
          </tr>
          <tr>
            <td style="padding:24px 34px;background-color:#eef3f0;border-top:1px solid #dce5df;text-align:center;">
              <p style="margin:0;color:#445149;font-size:13px;line-height:20px;">Para soporte, escriba a <a href="mailto:{safe_support_email}" style="color:#087c3f;font-weight:700;text-decoration:none;">{safe_support_email}</a>.</p>
              <p style="margin:13px 0 0;color:#173c27;font-size:13px;font-weight:700;line-height:20px;">{program_name}<br>Universidad Técnica Estatal de Quevedo</p>
              <p style="margin:15px 0 0;color:#7d8982;font-size:11px;line-height:16px;">Mensaje automático · {current_year}</p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""
    return plain_message, html_message


def generate_credentials_email(*, nombre, system_name, username, nueva_password):
    """Genera el correo institucional para credenciales nuevas o restablecidas."""
    current_year = datetime.datetime.now().year
    site_url = getattr(settings, 'SITE_URL', 'http://localhost:8000').rstrip('/')
    login_url = f"{site_url}/login/"
    support_email = getattr(
        settings, 'SUPPORT_EMAIL', 'olimpiadasmecanicauteq@gmail.com'
    )

    recipient_name = escape(str(nombre))
    system_label = escape(str(system_name))
    safe_username = escape(str(username))
    safe_password = escape(str(nueva_password))
    safe_support_email = escape(str(support_email))
    plain_message = f"""Estimado/a {nombre},

Se generaron nuevas credenciales de acceso para {system_name}.

Usuario: {username}
Contraseña: {nueva_password}

Acceda a la plataforma en: {login_url}

Por seguridad, no comparta estas credenciales. Si necesita ayuda, contacte a:
{support_email}

Atentamente,
Universidad Técnica Estatal de Quevedo
"""

    html_message = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Credenciales de acceso</title>
</head>
<body style="margin:0;padding:0;background-color:#f2f5f3;font-family:Arial,Helvetica,sans-serif;color:#1e2b25;">
  <div style="display:none;max-height:0;overflow:hidden;opacity:0;color:transparent;">
    Sus nuevas credenciales de acceso para EVAUTEQ están disponibles.
  </div>
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="width:100%;background-color:#f2f5f3;">
    <tr>
      <td align="center" style="padding:28px 12px;">
        <table role="presentation" width="620" cellspacing="0" cellpadding="0" border="0" style="width:100%;max-width:620px;background-color:#ffffff;border:1px solid #dce5df;">
          <tr>
            <td style="padding:32px 34px 28px;background-color:#087c3f;border-bottom:5px solid #f0a429;">
              <p style="margin:0 0 8px;color:#d7f0e0;font-size:12px;font-weight:700;letter-spacing:1.1px;text-transform:uppercase;">EVAUTEQ · Acceso seguro</p>
              <h1 style="margin:0;color:#ffffff;font-size:27px;line-height:34px;font-weight:700;">Credenciales de acceso</h1>
              <p style="margin:10px 0 0;color:#e6f5eb;font-size:15px;line-height:22px;">{system_label}</p>
            </td>
          </tr>
          <tr>
            <td style="padding:32px 34px 18px;">
              <p style="margin:0 0 16px;font-size:16px;line-height:24px;">Estimado/a <strong>{recipient_name}</strong>,</p>
              <p style="margin:0;font-size:15px;line-height:24px;color:#435149;">Hemos generado las credenciales que necesita para ingresar a la plataforma.</p>
            </td>
          </tr>
          <tr>
            <td style="padding:0 34px 22px;">
              <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="width:100%;border:1px solid #dce8e0;background-color:#f8fbf9;">
                <tr>
                  <td style="padding:15px 18px;border-left:4px solid #087c3f;">
                    <p style="margin:0;color:#66736c;font-size:11px;font-weight:700;letter-spacing:0.8px;text-transform:uppercase;">Usuario</p>
                    <p style="margin:7px 0 0;color:#173c27;font-family:Consolas,'Courier New',monospace;font-size:18px;font-weight:700;word-break:break-word;">{safe_username}</p>
                  </td>
                </tr>
                <tr>
                  <td style="padding:15px 18px;border-top:1px solid #dce8e0;border-left:4px solid #d68c00;background-color:#fff8e8;">
                    <p style="margin:0;color:#765000;font-size:11px;font-weight:700;letter-spacing:0.8px;text-transform:uppercase;">Contraseña temporal</p>
                    <p style="margin:7px 0 0;color:#79550a;font-family:Consolas,'Courier New',monospace;font-size:18px;font-weight:700;word-break:break-word;">{safe_password}</p>
                  </td>
                </tr>
              </table>
            </td>
          </tr>
          <tr>
            <td style="padding:0 34px 24px;">
              <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="width:100%;background-color:#fff8e8;border:1px solid #f4deb0;">
                <tr>
                  <td style="padding:15px 17px;border-left:4px solid #d68c00;">
                    <p style="margin:0 0 4px;color:#765000;font-size:14px;font-weight:700;">Proteja su acceso</p>
                    <p style="margin:0;color:#705a27;font-size:13px;line-height:19px;">No comparta estas credenciales ni reenvíe este correo. Si no solicitó este acceso, contacte al equipo de soporte.</p>
                  </td>
                </tr>
              </table>
            </td>
          </tr>
          <tr>
            <td align="center" style="padding:2px 34px 32px;">
              <a href="{login_url}" style="display:inline-block;padding:13px 22px;background-color:#087c3f;color:#ffffff;font-size:14px;font-weight:700;text-decoration:none;border-radius:4px;">Ingresar a EVAUTEQ</a>
            </td>
          </tr>
          <tr>
            <td style="padding:24px 34px;background-color:#eef3f0;border-top:1px solid #dce5df;text-align:center;">
              <p style="margin:0;color:#445149;font-size:13px;line-height:20px;">¿Necesita ayuda? Escriba a <a href="mailto:{safe_support_email}" style="color:#087c3f;font-weight:700;text-decoration:none;">{safe_support_email}</a>.</p>
              <p style="margin:13px 0 0;color:#173c27;font-size:13px;font-weight:700;line-height:20px;">Universidad Técnica Estatal de Quevedo</p>
              <p style="margin:15px 0 0;color:#7d8982;font-size:11px;line-height:16px;">Mensaje automático · {current_year}</p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""
    return plain_message, html_message

def generate_email_messages(subject, nombre, system_name, username, nueva_password, email_type='credentials', additional_content=None):
    """
    Función global para generar mensajes de correo electrónico en formato texto plano y HTML.
    
    Args:
        subject (str): Asunto del correo
        nombre (str): Nombre del destinatario
        system_name (str): Nombre del sistema
        username (str): Nombre de usuario
        nueva_password (str): Contraseña generada
        email_type (str): Tipo de correo ('credentials' o 'participants_list')
        additional_content (dict): Contenido adicional (para listas de participantes)
    
    Returns:
        tuple: (plain_message, html_message)
    """
    
    # Obtener el año actual y la URL de acceso
    current_year = datetime.datetime.now().year
    site_url = getattr(settings, 'SITE_URL', 'http://localhost:8000').rstrip('/')
    login_url = f"{site_url}/login/"
    
    if email_type == 'credentials':
        # Mensaje en texto plano para credenciales
        plain_message = f"""
        Estimado/a {nombre},

        Sus credenciales de acceso al {system_name} son las siguientes:

        Usuario: {username}
        Contraseña: {nueva_password}

        Puede acceder al sistema en {login_url} usando estas credenciales.

        Si tiene alguna pregunta o necesita ayuda, no dude en contactarnos al correo: olimpiadasmecanicauteq@gmail.com

        Atentamente,
        Carrera de Ingeniería Mecánica
        Universidad Técnica Estatal Quevedo
                """
        
        # Mensaje HTML moderno para credenciales
        html_message = f"""
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <link href="https://fonts.googleapis.com/css2?family=Open+Sans:wght@300;400;600;700;800&display=swap" rel="stylesheet">
            <title>Credenciales de Acceso</title>
            <style>
                * {{
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }}
                
                body {{
                    font-family: 'Open Sans', sans-serif;
                    line-height: 1.6;
                    color: #333;
                    background: #f4f4f4;
                    padding: 20px;
                }}
                
                .email-container {{
                    max-width: 600px;
                    margin: 0 auto;
                    background: white;
                    border-radius: 8px;
                    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                    overflow: hidden;
                    border: 1px solid #ddd;
                }}
                
                .header {{
                    background: linear-gradient(135deg, #025a27 0%, #034a2a 100%);
                    color: white;
                    padding: 30px 30px;
                    text-align: center;
                    position: relative;
                }}
                
                .header::after {{
                    content: '';
                    position: absolute;
                    bottom: 0;
                    left: 0;
                    right: 0;
                    height: 3px;
                    background: linear-gradient(90deg, #ffd700 0%, #ffed4e 50%, #ffd700 100%);
                }}
                
                .header h1 {{
                    font-size: 24px;
                    font-weight: 700;
                    margin: 0 0 10px 0;
                    letter-spacing: 0.5px;
                    text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
                }}
                
                .header h2 {{
                    font-size: 18px;
                    font-weight: 400;
                    margin: 0;
                    letter-spacing: 0.3px;
                    opacity: 0.95;
                    text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
                }}
                
                .content {{
                    padding: 40px 30px;
                }}
                
                .greeting {{
                    font-size: 16px;
                    margin-bottom: 25px;
                    color: #555;
                    font-weight: 400;
                }}
                
                .credentials-card {{
                    background: #f9f9f9;
                    border-radius: 8px;
                    padding: 25px;
                    margin: 25px 0;
                    border-left: 4px solid #025a27;
                }}
                
                .credentials-card h3 {{
                    color: #025a27;
                    font-size: 18px;
                    margin-bottom: 20px;
                    font-weight: 600;
                }}
                
                .credential-item {{
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: 12px 0;
                    border-bottom: 1px solid #e0e0e0;
                }}
                
                .credential-item:last-child {{
                    border-bottom: none;
                }}
                
                .credential-label {{
                    font-weight: 600;
                    color: #555;
                    font-size: 14px;
                    min-width: 120px;
                }}
                
                .credential-value {{
                    background: #fff;
                    padding: 8px 15px;
                    border-radius: 4px;
                    font-family: 'Courier New', monospace;
                    font-weight: 600;
                    color: #025a27;
                    border: 1px solid #ddd;
                    font-size: 14px;
                    flex: 1;
                    margin-left: 15px;
                    text-align: center;
                }}
                
                .info-box {{
                    background: #e8f5e8;
                    border-radius: 8px;
                    padding: 20px;
                    margin: 25px 0;
                    border-left: 4px solid #025a27;
                }}
                
                .info-box h4 {{
                    color: #025a27;
                    margin-bottom: 10px;
                    font-size: 16px;
                    font-weight: 600;
                }}
                
                .info-box p {{
                    color: #424242;
                    font-size: 14px;
                    font-weight: 400;
                }}
                
                .footer {{
                    background: #f4f4f4;
                    padding: 30px;
                    text-align: center;
                    border-top: 1px solid #ddd;
                }}
                
                .footer p {{
                    color: #666;
                    font-size: 14px;
                    font-weight: 400;
                }}
                
                .footer .signature {{
                    font-weight: 600;
                    color: #025a27;
                    margin-top: 10px;
                }}
                
                .logo {{
                    font-size: 18px;
                    font-weight: bold;
                    margin-bottom: 10px;
                    line-height: 1.3;
                }}
                
                @media (max-width: 600px) {{
                    body {{
                        padding: 10px;
                    }}
                    
                    .content {{
                        padding: 20px 15px;
                    }}
                    
                    .header {{
                        padding: 20px;
                    }}
                    
                    .credential-item {{
                        flex-direction: column;
                        align-items: flex-start;
                        gap: 8px;
                    }}
                    
                    .credential-value {{
                        margin-left: 0;
                        width: 100%;
                    }}
                }}
            </style>
        </head>
        <body>
            <div class="email-container">
                <div class="header">
                    <h1>Universidad Técnica Estatal de Quevedo</h1>
                    <h2>Olimpiada Intercolegial de Matemática {current_year}</h2>
                </div>
                
                <div class="content">
                    <h1 style="font-size: 28px; font-weight: 700; color: #025a27; text-align: center; margin-bottom: 10px;">Credenciales de Acceso</h1>
                    <div class="subtitle" style="font-size: 18px; color: #555; text-align: center; margin-bottom: 30px;">{system_name}</div>
                    
                    <div class="greeting">
                        Estimado/a <strong>{nombre}</strong>,
                    </div>
                    
                    <p>Hemos generado sus credenciales de acceso al <strong>{system_name}</strong>. 
                    A continuación encontrará la información necesaria para ingresar al sistema:</p>
                    
                    <div class="credentials-card">
                        <h3>Sus Credenciales</h3>
                        <div class="credential-item">
                            <span class="credential-label">Usuario:</span>
                            <span class="credential-value">{username}</span>
                        </div>
                        <div class="credential-item">
                            <span class="credential-label">Contraseña:</span>
                            <span class="credential-value">{nueva_password}</span>
                        </div>
                    </div>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{login_url}" style="background: #025a27; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; font-weight: 600; font-size: 16px;">Acceder al Sistema</a>
                    </div>
                    
                    <div class="info-box">
                        <h4>Información Importante</h4>
                        <p>• Guarde estas credenciales en un lugar seguro<br>
                        • No comparta su contraseña con otras personas<br>
                        • Puede cambiar su contraseña una vez que ingrese al sistema<br>
                        • Para soporte técnico, contacte: <a href="mailto:olimpiadasmecanicauteq@gmail.com" style="color: #025a27;">olimpiadasmecanicauteq@gmail.com</a></p>
                    </div>
                    
                    <p>Si tiene alguna pregunta o necesita ayuda, no dude en contactarnos. 
                    Estamos aquí para ayudarle.</p>
                </div>
                
                <div class="footer">
                    <p>Atentamente,</p>
                    <div class="signature">Carrera de Ingeniería Mecánica<br>Universidad Técnica Estatal Quevedo</div>
                    <p style="margin-top: 15px; font-size: 12px; color: #999;">
                        Este es un mensaje automático, por favor no responda a este correo.
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
    elif email_type == 'participants_list':
        # Mensaje en texto plano para lista de participantes
        plain_message = f"""
        Estimado/a {nombre},

        Adjunto encontrará la lista completa de participantes asignados al grupo "{system_name}".

        Total de participantes: {additional_content.get('total_participantes', 'N/A')}

        IMPORTANTE: Las contraseñas mostradas en la tabla son las credenciales actuales de los participantes.
        Los participantes pueden acceder a la plataforma usando su cédula como usuario y la contraseña que aparece en la tabla.

        Si tiene alguna pregunta o necesita información adicional, no dude en contactarnos al correo: olimpiadasmecanicauteq@gmail.com

        Atentamente,
        Carrera de Ingeniería Mecánica
        Universidad Técnica Estatal Quevedo
                """
        
        # Mensaje HTML moderno para lista de participantes
        html_message = f"""
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <link href="https://fonts.googleapis.com/css2?family=Open+Sans:wght@300;400;600;700;800&display=swap" rel="stylesheet">
            <title>Lista de Participantes</title>
            <style>
                * {{
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }}
                
                body {{
                    font-family: 'Open Sans', sans-serif;
                    line-height: 1.6;
                    color: #333;
                    background: #f4f4f4;
                    padding: 20px;
                }}
                
                .email-container {{
                    max-width: 800px;
                    margin: 0 auto;
                    background: white;
                    border-radius: 8px;
                    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                    overflow: hidden;
                    border: 1px solid #ddd;
                }}
                
                .header {{
                    background: linear-gradient(135deg, #025a27 0%, #034a2a 100%);
                    color: white;
                    padding: 30px 30px;
                    text-align: center;
                    position: relative;
                }}
                
                .header::after {{
                    content: '';
                    position: absolute;
                    bottom: 0;
                    left: 0;
                    right: 0;
                    height: 3px;
                    background: linear-gradient(90deg, #ffd700 0%, #ffed4e 50%, #ffd700 100%);
                }}
                
                .header h1 {{
                    font-size: 24px;
                    font-weight: 700;
                    margin: 0 0 10px 0;
                    letter-spacing: 0.5px;
                    text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
                }}
                
                .header h2 {{
                    font-size: 18px;
                    font-weight: 400;
                    margin: 0;
                    letter-spacing: 0.3px;
                    opacity: 0.95;
                    text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
                }}
                
                .content {{
                    padding: 40px 30px;
                }}
                
                .greeting {{
                    font-size: 16px;
                    margin-bottom: 25px;
                    color: #555;
                    font-weight: 400;
                }}
                
                .participants-table {{
                    margin: 30px 0;
                    border-radius: 8px;
                    overflow: hidden;
                    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                    border: 2px solid #025a27;
                }}
                
                .participants-table table {{
                    width: 100%;
                    border-collapse: collapse;
                    background: white;
                }}
                
                .participants-table th {{
                    background: #025a27;
                    color: white;
                    padding: 15px 10px;
                    text-align: left;
                    font-weight: 700;
                    font-size: 14px;
                    border-bottom: 2px solid #ddd;
                }}
                
                .participants-table td {{
                    padding: 12px 10px;
                    border-bottom: 1px solid #ddd;
                    font-size: 13px;
                    border-right: 1px solid #eee;
                }}
                
                .participants-table tr:nth-child(even) {{
                    background-color: #f9f9f9;
                }}
                
                .participants-table tr:hover {{
                    background-color: #e8f4fd;
                }}
                
                .info-box {{
                    background: #e8f5e8;
                    border-radius: 8px;
                    padding: 20px;
                    margin: 25px 0;
                    border-left: 4px solid #025a27;
                }}
                
                .info-box h4 {{
                    color: #025a27;
                    margin-bottom: 10px;
                    font-size: 16px;
                    font-weight: 600;
                }}
                
                .info-box ul {{
                    color: #025a27;
                    font-size: 14px;
                    padding-left: 20px;
                }}
                
                .info-box li {{
                    margin-bottom: 8px;
                }}
                
                .footer {{
                    background: #f4f4f4;
                    padding: 30px;
                    text-align: center;
                    border-top: 1px solid #ddd;
                }}
                
                .footer p {{
                    color: #666;
                    font-size: 14px;
                    font-weight: 400;
                }}
                
                .footer .signature {{
                    font-weight: 600;
                    color: #025a27;
                    margin-top: 10px;
                }}
                
                .logo {{
                    font-size: 18px;
                    font-weight: bold;
                    margin-bottom: 10px;
                    line-height: 1.3;
                }}
                
                @media (max-width: 600px) {{
                    body {{
                        padding: 10px;
                    }}
                    
                    .content {{
                        padding: 20px 15px;
                    }}
                    
                    .header {{
                        padding: 20px;
                    }}
                    
                    .participants-table {{
                        font-size: 12px;
                    }}
                    
                    .participants-table th,
                    .participants-table td {{
                        padding: 8px 5px;
                    }}
                }}
            </style>
        </head>
        <body>
            <div class="email-container">
                <div class="header">
                    <h1>Universidad Técnica Estatal de Quevedo</h1>
                    <h2>Olimpiada Intercolegial de Matemática {current_year}</h2>
                </div>
                
                <div class="content">
                    <h1 style="font-size: 28px; font-weight: 700; color: #025a27; text-align: center; margin-bottom: 10px;">Lista de Participantes</h1>
                    <div class="subtitle" style="font-size: 18px; color: #555; text-align: center; margin-bottom: 30px;">Grupo: {system_name}</div>
                    
                    <div class="greeting">
                        Estimado/a <strong>{nombre}</strong>,
                    </div>
                    
                    <p>Adjunto encontrará la lista completa de participantes asignados al grupo <strong>"{system_name}"</strong>.</p>
                    
                    <div class="participants-table">
                        {additional_content.get('participantes_html', '')}
                    </div>
                    
                    <div class="info-box">
                        <h4>Información</h4>
                        <ul>
                            <li><strong>Total de participantes:</strong> {additional_content.get('total_participantes', 'N/A')}</li>
                            <li><strong>IMPORTANTE:</strong> Las contraseñas mostradas en la tabla son las credenciales actuales de los participantes.</li>
                            <li>Los participantes pueden acceder a la plataforma usando su <strong>cédula como usuario</strong> y la <strong>contraseña que aparece en la tabla</strong>.</li>
                            <li>Para soporte técnico, contacte: <a href="mailto:olimpiadasmecanicauteq@gmail.com" style="color: #025a27;">olimpiadasmecanicauteq@gmail.com</a></li>
                        </ul>
                    </div>
                    
                    <p>Si tiene alguna pregunta o necesita información adicional, no dude en contactarnos. 
                    Estamos aquí para ayudarle.</p>
                </div>
                
                <div class="footer">
                    <p>Atentamente,</p>
                    <div class="signature">Carrera de Ingeniería Mecánica<br>Universidad Técnica Estatal Quevedo</div>
                    <p style="margin-top: 15px; font-size: 12px; color: #999;">
                        Este es un mensaje automático, por favor no responda a este correo.
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
    
    return plain_message, html_message 
