# Fase di spegnimento.

L'idea è sostituire lo sfondo nero con un'immagine per dare informazioni agli utilizzatori di
non togliere alimentazione al dispositivo fino a quando non è completamente spento.

L'immagine si trova in tools

## Creare un tema Plymouth personalizzato

`sudo mkdir -p /usr/share/plymouth/themes/pncrema`

`sudo cp immagine.png /usr/share/plymouth/themes/pncrema/sfondo.png`

## Crea il file tema Plymouth

`sudo vi /usr/share/plymouth/themes/pncrema/pncrema.plymouth`

```
[Plymouth Theme]
Name=PNCREMA
Description=Custom shutdown splash
ModuleName=script

[script]
ImageDir=/usr/share/plymouth/themes/pncrema
ScriptFile=/usr/share/plymouth/themes/pncrema/pncrema.script
```

## Crea lo script che mostra l’immagine

`sudo vi /usr/share/plymouth/themes/pncrema/pncrema.script`

```
wallpaper_image = Image("sfondo.png");
wallpaper_sprite = Sprite(wallpaper_image);

# Centra lo sfondo
wallpaper_sprite.SetX((Window.GetWidth()  - wallpaper_image.GetWidth())  / 2);
wallpaper_sprite.SetY((Window.GetHeight() - wallpaper_image.GetHeight()) / 2);
```