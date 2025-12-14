import React from 'react';
import clsx from 'clsx';

const Card = ({ 
  children, 
  title, 
  subtitle,
  actions,
  hover = false,
  className,
  headerClassName,
  bodyClassName,
  ...props 
}) => {
  const cardClasses = clsx(
    'card',
    hover && 'card-hover',
    className
  );
  
  return (
    <div className={cardClasses} {...props}>
      {(title || subtitle || actions) && (
        <div className={clsx('widget-header', headerClassName)}>
          <div>
            {title && (
              <h3 className="widget-title">{title}</h3>
            )}
            {subtitle && (
              <p className="text-xs text-gray-500 mt-1">{subtitle}</p>
            )}
          </div>
          {actions && (
            <div className="flex items-center gap-2">
              {actions}
            </div>
          )}
        </div>
      )}
      
      <div className={clsx('p-4', bodyClassName)}>
        {children}
      </div>
    </div>
  );
};

export default Card;
