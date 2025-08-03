// Configuración optimizada de CKEditor para manejo de imágenes desde Word
// Las variables globales (uploadImageUrl, etc.) ya están definidas en el template HTML

// Configuración base de CKEditor que usa las variables globales del template
window.ckeditorConfig = {
    extraPlugins: 'pastefromword,clipboard,uploadimage',
    removePlugins: 'exportpdf',
    allowedContent: true,
    forcePasteAsPlainText: false,
    pasteFromWordPromptCleanup: false,
    pasteFromWordRemoveFontStyles: false,
    pasteFromWordRemoveStyles: false,
    // Configuración crucial para imágenes del portapapeles
    clipboard_handleImages: true,
    // URLs para upload - usa la variable global del template
    get filebrowserUploadUrl() { return window.uploadImageUrl || '/upload-image/'; },
    get uploadUrl() { return window.uploadImageUrl || '/upload-image/'; },
    get imageUploadUrl() { return window.uploadImageUrl || '/upload-image/'; },
    // Configuración de pegado mejorada
    pasteFilter: null
};

// Plugin personalizado para manejo mejorado de imágenes
CKEDITOR.plugins.add('wordimagehandler', {
    init: function(editor) {
        // Evento principal de pegado simplificado y efectivo
        editor.on('paste', function(e) {
            if (!e.data) return;
            
            // Manejar archivos directos (drag & drop o pegado de archivos)
            if (e.data.dataTransfer && e.data.dataTransfer.files && e.data.dataTransfer.files.length > 0) {
                e.cancel();
                handleDirectFiles(editor, e.data.dataTransfer.files);
                return;
            }
            
            // Manejar HTML con imágenes base64 (típico de Word)
            if (e.data.dataValue) {
                const html = e.data.dataValue;
                const base64Images = extractBase64Images(html);
                
                if (base64Images.length > 0) {
                    e.cancel();
                    processImagesAndText(editor, html, base64Images);
                    return;
                }
            }
        });
        
        // Comando personalizado para insertar imagen
        editor.addCommand('insertCustomImage', {
            exec: function(editor) {
                const input = document.createElement('input');
                input.type = 'file';
                input.accept = 'image/*';
                input.style.display = 'none';
                document.body.appendChild(input);
                
                input.onchange = function(e) {
                    const file = e.target.files[0];
                    if (file) {
                        uploadSingleImage(editor, file);
                    }
                    document.body.removeChild(input);
                };
                
                input.click();
            }
        });
        
        // Agregar botón a la toolbar
        editor.ui.addButton('CustomImage', {
            label: 'Insertar Imagen',
            command: 'insertCustomImage',
            toolbar: 'insert'
        });
    }
});

// Función simplificada para extraer imágenes base64 del HTML
function extractBase64Images(html) {
    const images = [];
    
    // Patrón principal: Todas las imágenes base64
    const imageRegex = /<img[^>]*src\s*=\s*["']data:image\/([^;]+);base64,([^"']+)["'][^>]*>/gi;
    let match;
    
    while ((match = imageRegex.exec(html)) !== null) {
        images.push({
            fullMatch: match[0],
            imageType: match[1],
            base64Data: match[2],
            srcAttribute: match[0].match(/src\s*=\s*["'][^"']+["']/i)[0],
            isFormula: isLikelyFormula(match[0])
        });
    }
    
    return images;
}

// Función simplificada para determinar si una imagen es probablemente una fórmula matemática
function isLikelyFormula(imgTag) {
    // Verificar atributos obvios que sugieren fórmulas
    const formulaIndicators = [
        /equation/i,
        /math/i,
        /formula/i
    ];
    
    // Verificar dimensiones típicas de fórmulas (altura pequeña)
    const heightMatch = imgTag.match(/height\s*=\s*["']?(\d+)/i);
    
    if (heightMatch) {
        const height = parseInt(heightMatch[1]);
        // Las fórmulas de Word suelen tener altura menor a 50px
        if (height <= 50) {
            return true;
        }
    }
    
    // Verificar indicadores en el tag
    return formulaIndicators.some(pattern => pattern.test(imgTag));
}

// Función para manejar archivos directos
function handleDirectFiles(editor, files) {
    const imageFiles = Array.from(files).filter(file => file.type.startsWith('image/'));
    
    if (imageFiles.length === 0) {
        return;
    }
    
    const uploadPromises = imageFiles.map(file => uploadSingleImagePromise(file));
    
    if (uploadPromises.length > 0) {
        showLoadingMessage('Subiendo imágenes...');
        
        Promise.all(uploadPromises)
            .then(urls => {
                hideLoadingMessage();
                urls.forEach(url => {
                    editor.insertHtml(`<img src="${url}" alt="Imagen" style="max-width: 100%; height: auto; margin: 5px 0;" />`);
                });
                showSuccessMessage(`Se subieron ${urls.length} imagen(es) correctamente`);
            })
            .catch(error => {
                hideLoadingMessage();
                showErrorMessage('Error al subir las imágenes');
            });
    }
}

// Función principal para procesar imágenes y texto (simplificada y efectiva)
function processImagesAndText(editor, html, base64Images) {
    showLoadingMessage('Procesando imágenes...');
    
    // Crear promesas de upload para todas las imágenes
    const uploadPromises = base64Images.map((imageData, index) => {
        try {
            // Convertir base64 a blob
            const byteCharacters = atob(imageData.base64Data);
            const byteNumbers = new Array(byteCharacters.length);
            for (let i = 0; i < byteCharacters.length; i++) {
                byteNumbers[i] = byteCharacters.charCodeAt(i);
            }
            const byteArray = new Uint8Array(byteNumbers);
            const blob = new Blob([byteArray], {type: `image/${imageData.imageType}`});
            
            const filename = imageData.isFormula ? 
                `formula_${index + 1}.${imageData.imageType}` :
                `imagen_${index + 1}.${imageData.imageType}`;
            
            return uploadSingleImagePromise(blob, filename)
                .then(url => ({
                    originalTag: imageData.fullMatch,
                    newUrl: url,
                    isFormula: imageData.isFormula
                }));
        } catch (error) {
            return Promise.reject(error);
        }
    });
    
    // Procesar todas las imágenes
    Promise.all(uploadPromises)
        .then(results => {
            hideLoadingMessage();
            
            // Limpiar el HTML y reemplazar imágenes
            let cleanHtml = cleanTextAroundFormulas(html, base64Images);
            
            // Reemplazar cada imagen base64 con su URL del servidor
            results.forEach(result => {
                const newImgTag = createSimpleImgTag(result.newUrl, result.isFormula);
                cleanHtml = cleanHtml.replace(result.originalTag, newImgTag);
            });
            
            // Insertar el contenido limpio y procesado
            editor.insertHtml(cleanHtml);
            
            // Mensaje de éxito
            const formulas = results.filter(r => r.isFormula).length;
            const images = results.length - formulas;
            
            if (formulas > 0 && images > 0) {
                showSuccessMessage(`Procesadas ${formulas} fórmula(s) y ${images} imagen(es)`);
            } else if (formulas > 0) {
                showSuccessMessage(`Procesadas ${formulas} fórmula(s) matemática(s)`);
            } else {
                showSuccessMessage(`Procesadas ${images} imagen(es)`);
            }
        })
        .catch(error => {
            hideLoadingMessage();
            showErrorMessage('Error al procesar las imágenes');
            // Fallback: insertar HTML original
            editor.insertHtml(html);
        });
}

// Función para crear un tag img optimizado
function createOptimizedImgTag(originalTag, newUrl, isFormula) {
    // Extraer atributos importantes del tag original
    const altMatch = originalTag.match(/alt\s*=\s*["']([^"']*)["']/i);
    const titleMatch = originalTag.match(/title\s*=\s*["']([^"']*)["']/i);
    const classMatch = originalTag.match(/class\s*=\s*["']([^"']*)["']/i);
    const styleMatch = originalTag.match(/style\s*=\s*["']([^"']*)["']/i);
    const widthMatch = originalTag.match(/width\s*=\s*["']?([^"'\s>]+)/i);
    const heightMatch = originalTag.match(/height\s*=\s*["']?([^"'\s>]+)/i);
    
    // Construir el nuevo tag
    let newTag = `<img src="${newUrl}"`;
    
    // Agregar alt apropiado
    if (altMatch && altMatch[1]) {
        newTag += ` alt="${altMatch[1]}"`;
    } else if (isFormula) {
        newTag += ` alt="Fórmula matemática"`;
    } else {
        newTag += ` alt="Imagen"`;
    }
    
    // Preservar dimensiones si existen y son razonables
    if (widthMatch && heightMatch) {
        const width = parseInt(widthMatch[1]);
        const height = parseInt(heightMatch[1]);
        
        if (width > 0 && width <= 1000 && height > 0 && height <= 1000) {
            newTag += ` width="${width}" height="${height}"`;
        }
    }
    
    // Preservar clase si existe
    if (classMatch && classMatch[1]) {
        newTag += ` class="${classMatch[1]}"`;
    }
    
    // Estilo optimizado
    let style = '';
    if (styleMatch && styleMatch[1]) {
        style = styleMatch[1];
    }
    
    // Agregar estilos por defecto para fórmulas
    if (isFormula) {
        const additionalStyle = 'vertical-align: middle; margin: 0 2px;';
        style = style ? `${style} ${additionalStyle}` : additionalStyle;
    } else {
        const additionalStyle = 'max-width: 100%; height: auto;';
        style = style ? `${style} ${additionalStyle}` : additionalStyle;
    }
    
    newTag += ` style="${style}"`;
    
    // Preservar título si existe
    if (titleMatch && titleMatch[1]) {
        newTag += ` title="${titleMatch[1]}"`;
    }
    
    newTag += ' />';
    
    return newTag;
}

// Función para limpiar texto duplicado alrededor de fórmulas (versión conservadora)
function cleanTextAroundFormulas(html, base64Images) {
    let cleanHtml = html;
    
    // Solo limpiar texto que esté claramente adyacente a las fórmulas y que sea duplicado
    base64Images.forEach(imageData => {
        if (imageData.isFormula) {
            // Buscar texto inmediatamente antes y después de la imagen
            const imgIndex = cleanHtml.indexOf(imageData.fullMatch);
            if (imgIndex !== -1) {
                // Buscar patrones específicos de texto duplicado común en fórmulas de Word
                const duplicatePatterns = [
                    // Patrones específicos como el ejemplo: mn20mn+122mn+4+22mn+2
                    /[a-z]*\d*[a-z]*\d*[+\-]\d*[a-z]*\d*[+\-]?\d*[a-z]*\d*/g,
                    // Texto con raíces cuadradas sin la imagen
                    /√\d*[a-z]*\d*[+\-]?\d*/g
                ];
                
                duplicatePatterns.forEach(pattern => {
                    // Solo buscar en un rango pequeño alrededor de la imagen (50 caracteres)
                    const beforeStart = Math.max(0, imgIndex - 50);
                    const beforeText = cleanHtml.substring(beforeStart, imgIndex);
                    const afterText = cleanHtml.substring(imgIndex + imageData.fullMatch.length, imgIndex + imageData.fullMatch.length + 50);
                    
                    // Limpiar texto duplicado antes de la imagen
                    const beforeMatch = beforeText.match(pattern);
                    if (beforeMatch) {
                        beforeMatch.forEach(match => {
                            if (match.length > 5) { // Solo limpiar cadenas largas
                                cleanHtml = cleanHtml.replace(match, '');
                            }
                        });
                    }
                    
                    // Limpiar texto duplicado después de la imagen
                    const afterMatch = afterText.match(pattern);
                    if (afterMatch) {
                        afterMatch.forEach(match => {
                            if (match.length > 5) { // Solo limpiar cadenas largas
                                cleanHtml = cleanHtml.replace(match, '');
                            }
                        });
                    }
                });
            }
        }
    });
    
    // Limpiar espacios múltiples
    cleanHtml = cleanHtml.replace(/\s{2,}/g, ' ');
    
    return cleanHtml;
}

// Función para crear un tag img simple y efectivo
function createSimpleImgTag(url, isFormula) {
    let imgTag = `<img src="${url}"`;
    
    if (isFormula) {
        imgTag += ` alt="Fórmula matemática" style="vertical-align: middle; margin: 0 2px;"`;
    } else {
        imgTag += ` alt="Imagen" style="max-width: 100%; height: auto;"`;
    }
    
    imgTag += ' />';
    return imgTag;
}

// Funciones de detección de Word removidas - funcionalidad simplificada

// Función para subir una sola imagen
function uploadSingleImage(editor, file) {
    // Validar que la URL esté definida
    if (!window.uploadImageUrl) {
        showErrorMessage('Error de configuración: URL de upload no encontrada');
        return;
    }
    
    const formData = new FormData();
    formData.append('upload', file);
    
    fetch(window.uploadImageUrl, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.url) {
            editor.insertHtml(`<img src="${data.url}" alt="Imagen" style="max-width: 100%; height: auto;" />`);
        } else {
            showErrorMessage('No se pudo subir la imagen');
        }
    })
    .catch(error => {
        showErrorMessage('Error al subir la imagen');
    });
}

// Función para subir imagen como promesa
function uploadSingleImagePromise(file, filename = null) {
    // Validar que la URL esté definida
    if (!window.uploadImageUrl) {
        return Promise.reject(new Error('URL de upload no configurada'));
    }
    
    const formData = new FormData();
    formData.append('upload', file, filename || file.name || 'image.png');
    
    return fetch(window.uploadImageUrl, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: formData
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.url) {
            return data.url;
        } else {
            throw new Error('No se recibió URL en la respuesta');
        }
    });
}

// Funciones de utilidad simplificadas (sin alertas)
function showLoadingMessage(message) {
    // Silencioso - sin alertas
}

function hideLoadingMessage() {
    // Silencioso - sin alertas
}

function showSuccessMessage(message) {
    // Silencioso - sin alertas
}

function showErrorMessage(message) {
    // Silencioso - sin alertas
}

// Función para obtener el token CSRF
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}



// Inicialización cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    // Cargar el plugin personalizado si CKEditor está disponible
    if (window.CKEDITOR) {
        // Agregar el plugin al registro de plugins
        window.ckeditorConfig.extraPlugins += ',wordimagehandler';
    }
});