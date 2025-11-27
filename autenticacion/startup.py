from autenticacion.models import UsuarioPersonalizado

def reset_root_password():
    if not UsuarioPersonalizado.objects.filter(username='root').exists():
        UsuarioPersonalizado.objects.create_superuser(
            username='root',
            email='root@syncro.local',
            password='Syncro2025!'
        )
        print('✅ Superusuario root creado')
    else:
        u = UsuarioPersonalizado.objects.get(username='root')
        u.set_password('Syncro2025!')
        u.is_superuser = True
        u.is_staff = True
        u.save()
        print('✅ Contraseña de root actualizada a Syncro2025!')