import { useSelector, useDispatch } from 'react-redux';
import { RootState, AppDispatch } from '../app/store';
import { setLogin, setLogout } from '../features/authentication/authSlice';
import { User } from '../types';

export const useAuth = () => {
  const dispatch = useDispatch<AppDispatch>();
  const { isAuthenticated, user, token } = useSelector(
    (state: RootState) => state.auth
  );

  const login = (userData: User, userToken: string) => {
    dispatch(setLogin({ user: userData, token: userToken }));
  };

  const logout = () => {
    dispatch(setLogout());
  };

  return { isAuthenticated, user, token, login, logout };
};